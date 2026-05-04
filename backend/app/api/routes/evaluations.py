from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.evaluation import Evaluation
from app.schemas.auth import CurrentUser
from app.schemas.evaluation import EvaluationCreate, EvaluationRead

router = APIRouter()


@router.post("", response_model=EvaluationRead)
def create_evaluation(
    payload: EvaluationCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Evaluation:
    evaluation = Evaluation(
        company_id=current_user.company_id,
        title=payload.title,
        description=payload.description,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        created_by=current_user.id,
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return evaluation


@router.get("", response_model=list[EvaluationRead])
def list_evaluations(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Evaluation]:
    return list(
        db.scalars(
            select(Evaluation)
            .where(Evaluation.company_id == current_user.company_id)
            .order_by(Evaluation.created_at.desc())
        )
    )


@router.get("/{evaluation_id}", response_model=EvaluationRead)
def get_evaluation(
    evaluation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Evaluation:
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation or evaluation.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return evaluation
