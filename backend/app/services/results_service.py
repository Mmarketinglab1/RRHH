from collections import defaultdict
from statistics import median, pstdev
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evaluation import Competency, Question
from app.models.participant import EvaluatorAssignment, Participant
from app.models.response import Response
from app.schemas.result import CompetencyResult, EvaluationResults, ParticipantRanking


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def _median(values: list[float]) -> float:
    return round(float(median(values)), 2) if values else 0.0


def _stddev(values: list[float]) -> float:
    return round(float(pstdev(values)), 2) if len(values) > 1 else 0.0


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

    for response, _question, competency, assignment, participant in rows:
        weighted_score = float(response.score) * float(assignment.weight)
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
        bucket["scores"].append(float(response.score))
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

    return EvaluationResults(
        evaluation_id=evaluation_id,
        average=_avg(all_scores),
        median=_median(all_scores),
        stddev=_stddev(all_scores),
        competencies=competency_results,
        ranking=ranking,
    )
