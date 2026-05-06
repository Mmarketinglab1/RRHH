from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.evaluation import Competency, Evaluation, Question
from app.schemas.auth import CurrentUser
from app.schemas.evaluation import (
    CompetencyCreate,
    CompetencyRead,
    CompetencyUpdate,
    QuestionCreate,
    QuestionRead,
    QuestionUpdate,
)

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


@router.patch("/{evaluation_id}/competencies/{competency_id}", response_model=CompetencyRead)
def update_competency(
    evaluation_id: UUID,
    competency_id: UUID,
    payload: CompetencyUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Competency:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    competency = db.get(Competency, competency_id)
    if (
        not competency
        or competency.company_id != current_user.company_id
        or competency.evaluation_id != evaluation_id
    ):
        raise HTTPException(status_code=404, detail="Competency not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(competency, field, value)
    db.commit()
    db.refresh(competency)
    return competency


@router.delete("/{evaluation_id}/competencies/{competency_id}", status_code=204)
def delete_competency(
    evaluation_id: UUID,
    competency_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    competency = db.get(Competency, competency_id)
    if (
        not competency
        or competency.company_id != current_user.company_id
        or competency.evaluation_id != evaluation_id
    ):
        raise HTTPException(status_code=404, detail="Competency not found")

    db.delete(competency)
    db.commit()


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


@router.patch("/{evaluation_id}/questions/{question_id}", response_model=QuestionRead)
def update_question(
    evaluation_id: UUID,
    question_id: UUID,
    payload: QuestionUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Question:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    question = db.get(Question, question_id)
    if (
        not question
        or question.company_id != current_user.company_id
        or question.evaluation_id != evaluation_id
    ):
        raise HTTPException(status_code=404, detail="Question not found")

    updates = payload.model_dump(exclude_unset=True)
    if "competency_id" in updates:
        competency = db.get(Competency, updates["competency_id"])
        if (
            not competency
            or competency.company_id != current_user.company_id
            or competency.evaluation_id != evaluation_id
        ):
            raise HTTPException(status_code=404, detail="Competency not found")
    for field, value in updates.items():
        setattr(question, field, value)
    db.commit()
    db.refresh(question)
    return question


@router.delete("/{evaluation_id}/questions/{question_id}", status_code=204)
def delete_question(
    evaluation_id: UUID,
    question_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    question = db.get(Question, question_id)
    if (
        not question
        or question.company_id != current_user.company_id
        or question.evaluation_id != evaluation_id
    ):
        raise HTTPException(status_code=404, detail="Question not found")

    db.delete(question)
    db.commit()
