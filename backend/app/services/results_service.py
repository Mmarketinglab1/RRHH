from collections import defaultdict
from statistics import median, pstdev
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evaluation import Competency, Question
from app.models.participant import EvaluatorAssignment, Participant
from app.models.response import Response
from app.schemas.result import CompetencyResult, EvaluationResults, ParticipantRanking, QuestionResult


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def _median(values: list[float]) -> float:
    return round(float(median(values)), 2) if values else 0.0


def _stddev(values: list[float]) -> float:
    return round(float(pstdev(values)), 2) if len(values) > 1 else 0.0


def _map_response_to_score(response: Response, question: Question) -> float | None:
    if not question.is_evaluative:
        return None

    # Handle numeric_1_10
    if question.question_type == "numeric_1_10":
        return float(response.score) if response.score is not None else None

    # Handle NPS
    if question.question_type == "nps":
        return float(response.score) if response.score is not None else None

    # Handle Dicotomic
    if question.question_type == "dicotomic":
        if response.selected_option:
            opt = response.selected_option.strip().lower()
            if opt in ("sí", "si", "verdadero", "yes", "true"):
                return 10.0
            if opt in ("no", "falso", "false"):
                return 1.0
        return float(response.score) if response.score is not None else None

    # Handle Likert
    if question.question_type == "likert":
        if response.selected_option and question.options:
            try:
                options_list = list(question.options)
                idx = options_list.index(response.selected_option)
                if len(options_list) > 1:
                    return round((idx / (len(options_list) - 1)) * 9 + 1, 2)
                return 10.0
            except (ValueError, TypeError):
                pass
        return float(response.score) if response.score is not None else None

    # Handle Semantic Differential
    if question.question_type == "semantic_differential":
        if response.score is not None:
            steps = 7
            if question.options and isinstance(question.options, dict):
                steps = question.options.get("steps", 7)
            if steps > 1:
                return round(((response.score - 1) / (steps - 1)) * 9 + 1, 2)
            return 10.0
        return None

    return None


def calculate_evaluation_results(
    db: Session, company_id: UUID, evaluation_id: UUID
) -> EvaluationResults:
    rows = db.execute(
        select(Response, Question, Competency, EvaluatorAssignment, Participant)
        .join(Question, Question.id == Response.question_id)
        .join(Competency, Competency.id == Question.competency_id)
        .join(EvaluatorAssignment, EvaluatorAssignment.id == Response.assignment_id)
        .join(Participant, Participant.id == EvaluatorAssignment.evaluatee_id)
        .where(
            Response.company_id == company_id,
            Response.evaluation_id == evaluation_id,
        )
    ).all()

    all_scores: list[float] = []
    by_competency: dict[UUID, dict] = {}
    by_participant: dict[UUID, dict] = defaultdict(lambda: {"name": "", "scores": []})

    # Question-specific raw data
    by_question: dict[UUID, dict] = {}

    for response, question, competency, assignment, participant in rows:
        # 1. Initialize question stats bucket if not exists
        if question.id not in by_question:
            # Initialize distribution based on type
            distribution = {}
            if question.options and isinstance(question.options, list):
                distribution = {str(opt): 0 for opt in question.options}
            elif question.question_type == "dicotomic":
                distribution = {"Sí": 0, "No": 0}
            elif question.question_type == "likert":
                distribution = {
                    "Muy en desacuerdo": 0,
                    "En desacuerdo": 0,
                    "Neutral": 0,
                    "De acuerdo": 0,
                    "Muy de acuerdo": 0,
                }
            elif question.question_type == "nps":
                distribution = {"Promotores (9-10)": 0, "Pasivos (7-8)": 0, "Detractores (0-6)": 0}
            elif question.question_type == "semantic_differential":
                steps = 7
                if question.options and isinstance(question.options, dict):
                    steps = question.options.get("steps", 7)
                distribution = {str(i): 0 for i in range(1, steps + 1)}
            elif question.question_type == "numeric_1_10":
                distribution = {str(i): 0 for i in range(1, 11)}

            by_question[question.id] = {
                "text": question.text,
                "type": question.question_type,
                "is_evaluative": question.is_evaluative,
                "competency_name": competency.name,
                "scores": [],
                "distribution": distribution,
                "responses_count": 0,
            }

        q_bucket = by_question[question.id]
        q_bucket["responses_count"] += 1

        # 2. Process distribution
        q_type = question.question_type
        if q_type == "nps" and response.score is not None:
            score_val = response.score
            if score_val >= 9:
                q_bucket["distribution"]["Promotores (9-10)"] += 1
            elif score_val >= 7:
                q_bucket["distribution"]["Pasivos (7-8)"] += 1
            else:
                q_bucket["distribution"]["Detractores (0-6)"] += 1
        elif q_type in ("numeric_1_10", "semantic_differential") and response.score is not None:
            key = str(response.score)
            q_bucket["distribution"][key] = q_bucket["distribution"].get(key, 0) + 1
        elif q_type in ("dicotomic", "single_choice", "likert", "frequency", "categorization") and response.selected_option:
            # Map Sí/Yes/Verdadero to Sí and No/False/Falso to No for dicotomic distribution key
            val = str(response.selected_option)
            if q_type == "dicotomic":
                if val.lower() in ("sí", "si", "verdadero", "yes", "true"):
                    val = "Sí"
                elif val.lower() in ("no", "falso", "false"):
                    val = "No"
            q_bucket["distribution"][val] = q_bucket["distribution"].get(val, 0) + 1
        elif q_type in ("multiple_choice", "checklist") and response.selected_options:
            for opt in response.selected_options:
                val = str(opt)
                q_bucket["distribution"][val] = q_bucket["distribution"].get(val, 0) + 1
        elif q_type == "ranking" and response.selected_options:
            if len(response.selected_options) > 0:
                first_choice = str(response.selected_options[0])
                q_bucket["distribution"][first_choice] = q_bucket["distribution"].get(first_choice, 0) + 1

        # 3. Process scoring (if evaluative)
        score = _map_response_to_score(response, question)
        if score is not None:
            q_bucket["scores"].append(score)

            weighted_score = score * float(assignment.weight)
            all_scores.append(weighted_score)

            bucket = by_competency.setdefault(
                competency.id,
                {
                    "name": competency.name,
                    "weight": float(competency.weight),
                    "scores": [],
                    "weighted_scores": [],
                },
            )
            bucket["scores"].append(score)
            bucket["weighted_scores"].append(weighted_score * float(competency.weight))

            participant_bucket = by_participant[participant.id]
            participant_bucket["name"] = participant.full_name
            participant_bucket["scores"].append(weighted_score)

    competency_results = [
        CompetencyResult(
            competency_id=competency_id,
            competency_name=data["name"],
            average=_avg(data["scores"]),
            weighted_average=_avg(data["weighted_scores"]),
            median=_median(data["scores"]),
            stddev=_stddev(data["scores"]),
            responses=len(data["scores"]),
        )
        for competency_id, data in by_competency.items()
    ]

    ranked = sorted(
        (
            {
                "participant_id": participant_id,
                "participant_name": data["name"],
                "average": _avg(data["scores"]),
            }
            for participant_id, data in by_participant.items()
        ),
        key=lambda item: item["average"],
        reverse=True,
    )

    ranking = [
        ParticipantRanking(
            participant_id=item["participant_id"],
            participant_name=item["participant_name"],
            average=item["average"],
            rank=index + 1,
        )
        for index, item in enumerate(ranked)
    ]

    question_results = [
        QuestionResult(
            question_id=q_id,
            question_text=data["text"],
            question_type=data["type"],
            is_evaluative=data["is_evaluative"],
            competency_name=data["competency_name"],
            average=_avg(data["scores"]) if data["is_evaluative"] else None,
            median=_median(data["scores"]) if data["is_evaluative"] else None,
            stddev=_stddev(data["scores"]) if data["is_evaluative"] else None,
            responses_count=data["responses_count"],
            distribution=data["distribution"],
        )
        for q_id, data in by_question.items()
    ]

    return EvaluationResults(
        evaluation_id=evaluation_id,
        average=_avg(all_scores),
        median=_median(all_scores),
        stddev=_stddev(all_scores),
        competencies=competency_results,
        ranking=ranking,
        questions=question_results,
    )
