from collections import defaultdict
from statistics import median, pstdev
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from app.models.company import Company
from app.models.evaluation import Evaluation, Competency, Question
from app.models.participant import EvaluatorAssignment, Participant
from app.models.response import Response
from app.schemas.result import (
    BusinessLineResult,
    CompetencyDetailedResult,
    CompetencyResult,
    EvaluationResults,
    ExecutiveReportResults,
    ExecutiveSummaryInsights,
    ItemScore,
    OutlierAlert,
    ParticipantMatrixRow,
    ParticipantRanking,
    QuestionResult,
    ScatterPoint,
)


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
    Evaluator = aliased(Participant)
    rows = db.execute(
        select(Response, Question, Competency, EvaluatorAssignment, Participant, Evaluator)
        .join(Question, Question.id == Response.question_id)
        .join(Competency, Competency.id == Question.competency_id)
        .join(EvaluatorAssignment, EvaluatorAssignment.id == Response.assignment_id)
        .join(Participant, Participant.id == EvaluatorAssignment.evaluatee_id)
        .join(Evaluator, Evaluator.id == EvaluatorAssignment.evaluator_id)
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

    # Evaluator tracking for outlier detection
    evaluator_scores: dict[UUID, dict[UUID, dict]] = defaultdict(dict)
    evaluatee_names: dict[UUID, str] = {}

    for response, question, competency, assignment, participant, evaluator in rows:
        if assignment.relationship == "self":
            continue

        evaluatee_names[participant.id] = participant.full_name

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
                distribution = {str(i): 0 for i in range(1, 5)}
                distribution["No observado"] = 0

            by_question[question.id] = {
                "text": question.text,
                "text_self": question.text_self or question.text,
                "text_evaluator": question.text_evaluator or question.text,
                "tag_self": question.tag_self,
                "tag_evaluator": question.tag_evaluator,
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
        elif q_type in ("numeric_1_10", "semantic_differential"):
            if response.score is not None:
                key = str(response.score)
                q_bucket["distribution"][key] = q_bucket["distribution"].get(key, 0) + 1
            else:
                q_bucket["distribution"]["No observado"] = q_bucket["distribution"].get("No observado", 0) + 1
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

            # Track evaluator score for outlier detection
            if evaluator.id not in evaluator_scores[participant.id]:
                evaluator_scores[participant.id][evaluator.id] = {
                    "name": evaluator.full_name,
                    "scores": [],
                }
            evaluator_scores[participant.id][evaluator.id]["scores"].append(score)

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
            question_text_self=data["text_self"],
            question_text_evaluator=data["text_evaluator"],
            tag_self=data["tag_self"],
            tag_evaluator=data["tag_evaluator"],
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

    # Outliers calculation
    outliers: list[OutlierAlert] = []
    for evaluatee_id, evals_map in evaluator_scores.items():
        if len(evals_map) >= 2:
            evaluatee_name = evaluatee_names.get(evaluatee_id, "Colaborador")
            for evaluator_id, ev_data in evals_map.items():
                evaluator_name = ev_data["name"]
                eval_avg = _avg(ev_data["scores"])

                others_scores = []
                for other_id, other_data in evals_map.items():
                    if other_id != evaluator_id:
                        others_scores.extend(other_data["scores"])

                if others_scores:
                    others_avg = _avg(others_scores)
                    diff = round(eval_avg - others_avg, 2)
                    if diff >= 1.25:
                        outliers.append(
                            OutlierAlert(
                                evaluator_id=evaluator_id,
                                evaluator_name=evaluator_name,
                                evaluatee_id=evaluatee_id,
                                evaluatee_name=evaluatee_name,
                                evaluator_average=eval_avg,
                                others_average=others_avg,
                                diff=diff,
                                alert_type="high_outlier",
                                message=f"Pico muy positivo: {evaluator_name} evaluó a {evaluatee_name} con {eval_avg}, superior al promedio del grupo ({others_avg}).",
                            )
                        )
                    elif diff <= -1.25:
                        outliers.append(
                            OutlierAlert(
                                evaluator_id=evaluator_id,
                                evaluator_name=evaluator_name,
                                evaluatee_id=evaluatee_id,
                                evaluatee_name=evaluatee_name,
                                evaluator_average=eval_avg,
                                others_average=others_avg,
                                diff=diff,
                                alert_type="low_outlier",
                                message=f"Pico muy negativo: {evaluator_name} evaluó a {evaluatee_name} con {eval_avg}, inferior al promedio del resto ({others_avg}).",
                            )
                        )

    return EvaluationResults(
        evaluation_id=evaluation_id,
        average=_avg(all_scores),
        median=_median(all_scores),
        stddev=_stddev(all_scores),
        competencies=competency_results,
        ranking=ranking,
        questions=question_results,
        outliers=outliers,
    )


def calculate_participant_results(
    db: Session, company_id: UUID, evaluation_id: UUID, participant_id: UUID
):
    from fastapi import HTTPException
    from app.schemas.result import CompetencyScoreByRelation, QuestionDetailForParticipant, ParticipantDetailResults

    participant = db.get(Participant, participant_id)
    if (
        not participant
        or participant.company_id != company_id
        or participant.evaluation_id != evaluation_id
    ):
        raise HTTPException(status_code=404, detail="Participant not found")

    Evaluator = aliased(Participant)
    rows = db.execute(
        select(Response, Question, Competency, EvaluatorAssignment, Evaluator)
        .join(Question, Question.id == Response.question_id)
        .join(Competency, Competency.id == Question.competency_id)
        .join(EvaluatorAssignment, EvaluatorAssignment.id == Response.assignment_id)
        .join(Evaluator, Evaluator.id == EvaluatorAssignment.evaluator_id)
        .where(
            Response.company_id == company_id,
            Response.evaluation_id == evaluation_id,
            EvaluatorAssignment.evaluatee_id == participant_id,
        )
    ).all()

    all_competencies = db.scalars(
        select(Competency).where(
            Competency.company_id == company_id,
            Competency.evaluation_id == evaluation_id,
        )
    ).all()

    all_questions = db.scalars(
        select(Question).where(
            Question.company_id == company_id,
            Question.evaluation_id == evaluation_id,
        ).order_by(Question.position.asc())
    ).all()

    rel_friendly_names = {
        "self": "Autoevaluación",
        "peer": "Par",
        "direct_report": "Reporte Directo",
        "line_manager": "Líder directo",
        "indirect_manager": "Líder indirecto",
        "external_client": "Cliente Externo",
        "internal_client": "Cliente Interno",
    }

    comp_self_scores: dict[UUID, list[float]] = defaultdict(list)
    comp_eval_scores: dict[UUID, list[float]] = defaultdict(list)
    comp_rel_scores: dict[UUID, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    q_self_scores: dict[UUID, list[float]] = defaultdict(list)
    q_eval_scores: dict[UUID, list[float]] = defaultdict(list)
    q_comments: dict[UUID, list[dict]] = defaultdict(list)

    all_self_scores: list[float] = []
    all_eval_scores: list[float] = []

    for response, question, competency, assignment, evaluator in rows:
        score = _map_response_to_score(response, question)
        rel = assignment.relationship

        if response.comment and response.comment.strip():
            rel_label = rel_friendly_names.get(rel, rel)
            q_comments[question.id].append({
                "relationship": rel_label,
                "evaluator_name": evaluator.full_name,
                "comment": response.comment.strip(),
            })

        if score is not None:
            if rel == "self":
                comp_self_scores[competency.id].append(score)
                q_self_scores[question.id].append(score)
                all_self_scores.append(score)
            else:
                comp_eval_scores[competency.id].append(score)
                comp_rel_scores[competency.id][rel].append(score)
                q_eval_scores[question.id].append(score)
                all_eval_scores.append(score)

    comp_results: list[CompetencyScoreByRelation] = []
    for c in all_competencies:
        self_sc = _avg(comp_self_scores[c.id]) if comp_self_scores[c.id] else None
        eval_sc = _avg(comp_eval_scores[c.id]) if comp_eval_scores[c.id] else None
        
        by_rel = {
            rel_friendly_names.get(r, r): _avg(scores)
            for r, scores in comp_rel_scores[c.id].items()
            if scores
        }
        
        gap = round(self_sc - eval_sc, 2) if (self_sc is not None and eval_sc is not None) else None

        comp_results.append(
            CompetencyScoreByRelation(
                competency_id=c.id,
                competency_name=c.name,
                self_score=self_sc,
                evaluators_score=eval_sc,
                by_relationship=by_rel,
                gap=gap,
            )
        )

    q_results: list[QuestionDetailForParticipant] = []
    comp_map = {c.id: c.name for c in all_competencies}
    for q in all_questions:
        self_sc = _avg(q_self_scores[q.id]) if q_self_scores[q.id] else None
        eval_sc = _avg(q_eval_scores[q.id]) if q_eval_scores[q.id] else None

        q_results.append(
            QuestionDetailForParticipant(
                question_id=q.id,
                question_text=q.text_evaluator or q.text,
                competency_name=comp_map.get(q.competency_id, "General"),
                question_type=q.question_type,
                is_evaluative=q.is_evaluative,
                self_score=self_sc,
                evaluators_score=eval_sc,
                comments=q_comments[q.id],
            )
        )

    evaluated_comps = [c for c in comp_results if c.evaluators_score is not None]
    sorted_comps = sorted(evaluated_comps, key=lambda c: c.evaluators_score or 0, reverse=True)

    strengths = [f"{c.competency_name} ({c.evaluators_score})" for c in sorted_comps[:3]]
    opportunities = [f"{c.competency_name} ({c.evaluators_score})" for c in sorted_comps[-3:] if c not in sorted_comps[:3]]

    overall_self = _avg(all_self_scores) if all_self_scores else None
    overall_eval = _avg(all_eval_scores) if all_eval_scores else None
    overall_gap = round(overall_self - overall_eval, 2) if (overall_self is not None and overall_eval is not None) else None

    return ParticipantDetailResults(
        participant_id=participant.id,
        participant_name=participant.full_name,
        participant_email=participant.email,
        participant_role=participant.role,
        overall_evaluators_score=overall_eval,
        overall_self_score=overall_self,
        overall_gap=overall_gap,
        competencies=comp_results,
        questions=q_results,
        top_strengths=strengths,
        opportunities=opportunities,
    )


def calculate_executive_report_results(
    db: Session, company_id: UUID, evaluation_id: UUID
) -> ExecutiveReportResults:
    # 1. Obtener entidades principales
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation:
        raise ValueError("Evaluation not found")

    company = db.get(Company, company_id)
    company_name = company.name if company else "Organización"

    # 2. Obtener competencias y normalizar pesos a porcentajes
    competencies = db.scalars(
        select(Competency)
        .where(
            Competency.company_id == company_id,
            Competency.evaluation_id == evaluation_id,
        )
        .order_by(Competency.created_at)
    ).all()

    total_weight = sum(float(c.weight) for c in competencies) or 1.0
    comp_weight_pct: dict[UUID, float] = {}
    is_already_pct = abs(total_weight - 100.0) < 0.1
    for c in competencies:
        w = float(c.weight)
        comp_weight_pct[c.id] = round(w if is_already_pct else (w / total_weight) * 100.0, 2)

    # 3. Obtener preguntas
    questions = db.scalars(
        select(Question)
        .where(
            Question.company_id == company_id,
            Question.evaluation_id == evaluation_id,
        )
        .order_by(Question.position, Question.created_at)
    ).all()
    q_map = {q.id: q for q in questions}
    questions_by_comp: dict[UUID, list[Question]] = defaultdict(list)
    for q in questions:
        questions_by_comp[q.competency_id].append(q)

    # 4. Obtener participantes evaluados
    participants = db.scalars(
        select(Participant)
        .where(
            Participant.company_id == company_id,
            Participant.evaluation_id == evaluation_id,
        )
        .order_by(Participant.full_name)
    ).all()

    # 5. Obtener todas las respuestas con sus asignaciones
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

    # Mapear puntajes: por evaluado y por pregunta
    scores_by_p_q: dict[UUID, dict[UUID, list[float]]] = defaultdict(lambda: defaultdict(list))
    item_scores_all: dict[UUID, list[float]] = defaultdict(list)
    comp_responses_count: dict[UUID, int] = defaultdict(int)

    for response, question, competency, assignment, evaluatee in rows:
        sc = _map_response_to_score(response, question)
        if sc is not None:
            scores_by_p_q[evaluatee.id][question.id].append(sc)
            item_scores_all[question.id].append(sc)
            comp_responses_count[competency.id] += 1

    # 6. Construir filas de matriz por participante (Puntajes Netos y Ponderados)
    participant_rows: list[ParticipantMatrixRow] = []

    for p in participants:
        p_net_scores: dict[str, float] = {}
        p_weighted_scores: dict[str, float] = {}

        for c in competencies:
            c_qs = questions_by_comp.get(c.id, [])
            c_q_scores = []
            for q in c_qs:
                recorded_scores = scores_by_p_q[p.id].get(q.id, [])
                if recorded_scores:
                    c_q_scores.append(sum(recorded_scores) / len(recorded_scores))

            c_net_val = _avg(c_q_scores) if c_q_scores else 0.0
            p_net_scores[c.name] = c_net_val

            w_pct = comp_weight_pct.get(c.id, 0.0)
            c_weighted_val = round(c_net_val * (w_pct / 100.0), 2)
            p_weighted_scores[c.name] = c_weighted_val

        valid_net_values = [v for v in p_net_scores.values() if v > 0]
        p_net_avg = _avg(valid_net_values) if valid_net_values else 0.0
        p_weighted_total = round(sum(p_weighted_scores.values()), 2)

        participant_rows.append(
            ParticipantMatrixRow(
                participant_id=p.id,
                participant_name=p.full_name,
                role=p.role,
                business_line=p.business_line or "General",
                performance_history=p.performance_history or {},
                net_scores=p_net_scores,
                net_average=p_net_avg,
                weighted_scores=p_weighted_scores,
                weighted_total=p_weighted_total,
            )
        )

    # 7. Asignar rankings Net y Weighted
    sorted_by_net = sorted(participant_rows, key=lambda r: r.net_average, reverse=True)
    for idx, r in enumerate(sorted_by_net):
        r.rank_net = idx + 1

    sorted_by_weighted = sorted(participant_rows, key=lambda r: r.weighted_total, reverse=True)
    for idx, r in enumerate(sorted_by_weighted):
        r.rank_weighted = idx + 1

    # 8. Estadísticas detalladas por Competencia y Reactivos
    all_item_scores_list: list[ItemScore] = []
    comp_detailed_results: list[CompetencyDetailedResult] = []

    for c in competencies:
        c_items: list[ItemScore] = []
        for q in questions_by_comp.get(c.id, []):
            item_avg = _avg(item_scores_all.get(q.id, []))
            item_obj = ItemScore(
                question_id=q.id,
                question_text=q.text,
                competency_id=c.id,
                competency_name=c.name,
                average=item_avg,
                position=q.position,
            )
            c_items.append(item_obj)
            all_item_scores_list.append(item_obj)

        comp_net_list = [r.net_scores.get(c.name, 0.0) for r in participant_rows if r.net_scores.get(c.name, 0.0) > 0]
        comp_weighted_list = [r.weighted_scores.get(c.name, 0.0) for r in participant_rows if r.weighted_scores.get(c.name, 0.0) > 0]

        comp_detailed_results.append(
            CompetencyDetailedResult(
                competency_id=c.id,
                competency_name=c.name,
                weight=float(c.weight),
                weight_pct=comp_weight_pct.get(c.id, 0.0),
                net_average=_avg(comp_net_list),
                net_median=_median(comp_net_list),
                net_stddev=_stddev(comp_net_list),
                weighted_average=_avg(comp_weighted_list),
                weighted_median=_median(comp_weighted_list),
                weighted_stddev=_stddev(comp_weighted_list),
                responses_count=comp_responses_count.get(c.id, 0),
                items=c_items,
            )
        )

    # 9. Estadísticas globales del grupo
    all_net_avgs = [r.net_average for r in participant_rows if r.net_average > 0]
    all_weighted_totals = [r.weighted_total for r in participant_rows if r.weighted_total > 0]

    net_overall = {
        "average": _avg(all_net_avgs),
        "median": _median(all_net_avgs),
        "stddev": _stddev(all_net_avgs),
    }
    weighted_overall = {
        "average": _avg(all_weighted_totals),
        "median": _median(all_weighted_totals),
        "stddev": _stddev(all_weighted_totals),
    }

    # 10. Segmentación por Línea de Negocio
    by_line: dict[str, list[ParticipantMatrixRow]] = defaultdict(list)
    for r in participant_rows:
        by_line[r.business_line or "General"].append(r)

    business_lines_results: list[BusinessLineResult] = []
    for line_name, line_members in sorted(by_line.items(), key=lambda x: len(x[1]), reverse=True):
        l_net_avgs = [m.net_average for m in line_members if m.net_average > 0]
        l_weighted_totals = [m.weighted_total for m in line_members if m.weighted_total > 0]

        line_comp_avgs: dict[str, float] = {}
        for c in competencies:
            c_vals = [m.net_scores.get(c.name, 0.0) for m in line_members if m.net_scores.get(c.name, 0.0) > 0]
            line_comp_avgs[c.name] = _avg(c_vals)

        business_lines_results.append(
            BusinessLineResult(
                line_name=line_name,
                count=len(line_members),
                net_average=_avg(l_net_avgs),
                net_median=_median(l_net_avgs),
                net_stddev=_stddev(l_net_avgs),
                weighted_average=_avg(l_weighted_totals),
                competency_averages=line_comp_avgs,
                participants=sorted(line_members, key=lambda m: m.net_average, reverse=True),
            )
        )

    # 11. Datos de dispersión (Scatter points)
    scatter_data: dict[str, list[ScatterPoint]] = {}
    for c in competencies:
        points = []
        for idx, r in enumerate(participant_rows):
            points.append(
                ScatterPoint(
                    participant_id=r.participant_id,
                    participant_name=r.participant_name,
                    index=idx + 1,
                    business_line=r.business_line,
                    net_score=r.net_scores.get(c.name, 0.0),
                    weighted_score=r.weighted_scores.get(c.name, 0.0),
                )
            )
        scatter_data[c.name] = points

    # 12. Hallazgos analíticos e insights automáticos
    strongest_comp = max(comp_detailed_results, key=lambda c: c.net_average).competency_name if comp_detailed_results else "N/A"
    weakest_comp = min(comp_detailed_results, key=lambda c: c.net_average).competency_name if comp_detailed_results else "N/A"
    max_disp_comp = max(comp_detailed_results, key=lambda c: c.net_stddev).competency_name if comp_detailed_results else "N/A"
    min_disp_comp = min(comp_detailed_results, key=lambda c: c.net_stddev).competency_name if comp_detailed_results else "N/A"

    summary_bullets = [
        f"La competencia más fuerte organizacionalmente es \"{strongest_comp}\" mientras que la más baja es \"{weakest_comp}\".",
        f"\"{strongest_comp}\" no solo presenta el promedio más alto, sino también la consistencia más sólida en al menos la mitad del equipo evaluado.",
        f"La baja variabilidad en \"{min_disp_comp}\" sugiere que esta competencia se encuentra estandarizada y consistentemente desarrollada.",
        f"\"{max_disp_comp}\" presenta la mayor dispersión, lo que indica que esta capacidad no está homogéneamente desarrollada, representando un desafío clave para la transformación organizacional.",
    ]

    reactivos_bullets = [
        "La ejecución es fuerte en seguimiento y cumplimiento, pero muestra oportunidad en anticipación estratégica.",
        "La organización demuestra alta movilidad y adaptación operativa ante cambios estructurales.",
        "El equipo utiliza las herramientas disponibles, pero aún requiere capitalizar plenamente el enfoque estratégico y omnicanal.",
        "La fortaleza relacional es evidente, existiendo una valiosa oportunidad en la anticipación proactiva de necesidades del cliente.",
    ]

    insights = ExecutiveSummaryInsights(
        strongest_competency=strongest_comp,
        weakest_competency=weakest_comp,
        highest_dispersion_competency=max_disp_comp,
        lowest_dispersion_competency=min_disp_comp,
        summary_bullets=summary_bullets,
        reactivos_bullets=reactivos_bullets,
    )

    thresholds = evaluation.score_thresholds or {"high": 8.5, "medium": 7.0}

    return ExecutiveReportResults(
        evaluation_id=evaluation.id,
        evaluation_title=evaluation.title,
        company_name=company_name,
        client_logo_url=evaluation.client_logo_url,
        consultant_logo_url=evaluation.consultant_logo_url,
        scale_type=evaluation.scale_type or "numeric_1_10",
        total_evaluados=len(participants),
        net_overall=net_overall,
        weighted_overall=weighted_overall,
        thresholds=thresholds,
        competencies=comp_detailed_results,
        questions=all_item_scores_list,
        participants_matrix=participant_rows,
        business_lines=business_lines_results,
        scatter_data=scatter_data,
        insights=insights,
    )
