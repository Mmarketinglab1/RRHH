from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.evaluation import Competency, Evaluation, Question
from app.models.report import AIReport
from app.schemas.ai import AIReportRead, GeneratedQuestion, GeneratedQuestionsResponse
from app.schemas.auth import CurrentUser
from app.services.ai_service import (
    generate_group_summary,
    generate_individual_insights,
    generate_questions_for_competencies,
)
from app.services.results_service import calculate_evaluation_results

router = APIRouter()


def _ensure_evaluation(db: Session, company_id: UUID, evaluation_id: UUID) -> None:
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation or evaluation.company_id != company_id:
        raise HTTPException(status_code=404, detail="Evaluation not found")


@router.post("/{evaluation_id}/ai/questions", response_model=GeneratedQuestionsResponse)
@limiter.limit("10/day")
def generate_questions(
    request: Request,
    evaluation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GeneratedQuestionsResponse:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    competencies = list(
        db.scalars(
            select(Competency).where(
                Competency.company_id == current_user.company_id,
                Competency.evaluation_id == evaluation_id,
            )
        )
    )
    if not competencies:
        raise HTTPException(status_code=400, detail="Create competencies first")

    generated = generate_questions_for_competencies(
        [
            {
                "id": str(item.id),
                "name": item.name,
                "description": item.description,
                "weight": float(item.weight),
            }
            for item in competencies
        ]
    )

    question_reads: list[GeneratedQuestion] = []
    for index, item in enumerate(generated):
        competency_id = UUID(str(item["competency_id"]))
        if competency_id not in {competency.id for competency in competencies}:
            continue
        question = Question(
            company_id=current_user.company_id,
            evaluation_id=evaluation_id,
            competency_id=competency_id,
            text=item["text"],
            position=index,
        )
        db.add(question)
        question_reads.append(GeneratedQuestion(competency_id=competency_id, text=item["text"]))

    db.commit()
    return GeneratedQuestionsResponse(questions=question_reads)


@router.post("/{evaluation_id}/ai/group-report", response_model=AIReportRead)
@limiter.limit("10/day")
def create_group_report(
    request: Request,
    evaluation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AIReportRead:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    results = calculate_evaluation_results(db, current_user.company_id, evaluation_id)
    content = generate_group_summary(results)
    report = AIReport(
        company_id=current_user.company_id,
        evaluation_id=evaluation_id,
        report_type="group",
        content=content,
    )
    db.add(report)
    db.commit()
    return AIReportRead(report_type=report.report_type, content=content)


@router.post("/{evaluation_id}/ai/participants/{participant_id}/report", response_model=AIReportRead)
@limiter.limit("10/day")
def create_individual_report(
    request: Request,
    evaluation_id: UUID,
    participant_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AIReportRead:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    results = calculate_evaluation_results(db, current_user.company_id, evaluation_id)
    content = generate_individual_insights(participant_id, results)
    report = AIReport(
        company_id=current_user.company_id,
        evaluation_id=evaluation_id,
        participant_id=participant_id,
        report_type="individual",
        content=content,
    )
    db.add(report)
    db.commit()
    return AIReportRead(report_type=report.report_type, content=content)
