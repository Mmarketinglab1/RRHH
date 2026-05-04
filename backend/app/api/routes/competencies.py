from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.evaluation import Competency, Evaluation, Question
from app.schemas.auth import CurrentUser
from app.schemas.evaluation import CompetencyCreate, CompetencyRead, QuestionCreate, QuestionRead

router = APIRouter()


def _ensure_evaluation(db: Session, company_id: UUID, evaluation_id: UUID) -> Evaluation:
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation or evaluation.company_id != company_id:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return evaluation


@router.post("/{evaluation_id}/competencies", response_model=CompetencyRead)
def create_competency(
    evaluation_id: UUID,
    payload: CompetencyCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Competency:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    competency = Competency(
        company_id=current_user.company_id,
        evaluation_id=evaluation_id,
        name=payload.name,
        description=payload.description,
        weight=payload.weight,
    )
    db.add(competency)
    db.commit()
    db.refresh(competency)
    return competency


@router.get("/{evaluation_id}/competencies", response_model=list[CompetencyRead])
def list_competencies(
    evaluation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Competency]:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    return list(
        db.scalars(
            select(Competency).where(
                Competency.company_id == current_user.company_id,
                Competency.evaluation_id == evaluation_id,
            )
        )
    )


@router.post("/{evaluation_id}/questions", response_model=QuestionRead)
def create_question(
    evaluation_id: UUID,
    payload: QuestionCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Question:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    competency = db.get(Competency, payload.competency_id)
    if not competency or competency.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Competency not found")

    question = Question(
        company_id=current_user.company_id,
        evaluation_id=evaluation_id,
        competency_id=payload.competency_id,
        text=payload.text,
        position=payload.position,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.get("/{evaluation_id}/questions", response_model=list[QuestionRead])
def list_questions(
    evaluation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Question]:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    return list(
        db.scalars(
            select(Question)
            .where(
                Question.company_id == current_user.company_id,
                Question.evaluation_id == evaluation_id,
            )
            .order_by(Question.position.asc())
        )
    )
