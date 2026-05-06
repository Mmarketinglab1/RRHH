from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.evaluation import Evaluation
from app.models.participant import EvaluatorAssignment, Participant
from app.schemas.auth import CurrentUser
from app.schemas.participant import (
    AssignmentCreate,
    AssignmentRead,
    CSVUploadResult,
    ParticipantCreate,
    ParticipantRead,
    ParticipantUpdate,
)
from app.services.csv_service import parse_participants_csv

router = APIRouter()


def _ensure_evaluation(db: Session, company_id: UUID, evaluation_id: UUID) -> None:
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation or evaluation.company_id != company_id:
        raise HTTPException(status_code=404, detail="Evaluation not found")


@router.post("/{evaluation_id}/participants", response_model=ParticipantRead)
def create_participant(
    evaluation_id: UUID,
    payload: ParticipantCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Participant:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    participant = Participant(
        company_id=current_user.company_id,
        evaluation_id=evaluation_id,
        email=payload.email.lower(),
        full_name=payload.full_name,
        role=payload.role,
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


@router.post("/{evaluation_id}/participants/csv", response_model=CSVUploadResult)
async def upload_participants_csv(
    evaluation_id: UUID,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CSVUploadResult:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    rows = parse_participants_csv((await file.read()).decode("utf-8-sig"))
    created = 0
    skipped = 0
    for row in rows:
        exists = db.scalar(
            select(Participant).where(
                Participant.company_id == current_user.company_id,
                Participant.evaluation_id == evaluation_id,
                Participant.email == row["email"],
            )
        )
        if exists:
            skipped += 1
            continue
        db.add(
            Participant(
                company_id=current_user.company_id,
                evaluation_id=evaluation_id,
                email=row["email"],
                full_name=row["full_name"],
                role=row["role"],
            )
        )
        created += 1
    db.commit()
    return CSVUploadResult(created=created, skipped=skipped)


@router.get("/{evaluation_id}/participants", response_model=list[ParticipantRead])
def list_participants(
    evaluation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Participant]:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    return list(
        db.scalars(
            select(Participant).where(
                Participant.company_id == current_user.company_id,
                Participant.evaluation_id == evaluation_id,
            )
        )
    )


@router.patch("/{evaluation_id}/participants/{participant_id}", response_model=ParticipantRead)
def update_participant(
    evaluation_id: UUID,
    participant_id: UUID,
    payload: ParticipantUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Participant:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    participant = db.get(Participant, participant_id)
    if (
        not participant
        or participant.company_id != current_user.company_id
        or participant.evaluation_id != evaluation_id
    ):
        raise HTTPException(status_code=404, detail="Participant not found")

    updates = payload.model_dump(exclude_unset=True)
    if "email" in updates and updates["email"] is not None:
        updates["email"] = updates["email"].lower()
    for field, value in updates.items():
        setattr(participant, field, value)
    db.commit()
    db.refresh(participant)
    return participant


@router.delete("/{evaluation_id}/participants/{participant_id}", status_code=204)
def delete_participant(
    evaluation_id: UUID,
    participant_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    participant = db.get(Participant, participant_id)
    if (
        not participant
        or participant.company_id != current_user.company_id
        or participant.evaluation_id != evaluation_id
    ):
        raise HTTPException(status_code=404, detail="Participant not found")

    db.delete(participant)
    db.commit()


@router.post("/{evaluation_id}/assignments", response_model=AssignmentRead)
def create_assignment(
    evaluation_id: UUID,
    payload: AssignmentCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EvaluatorAssignment:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    evaluatee = db.get(Participant, payload.evaluatee_id)
    evaluator = db.get(Participant, payload.evaluator_id)
    if (
        not evaluatee
        or not evaluator
        or evaluatee.company_id != current_user.company_id
        or evaluator.company_id != current_user.company_id
    ):
        raise HTTPException(status_code=404, detail="Participant not found")

    assignment = EvaluatorAssignment(
        company_id=current_user.company_id,
        evaluation_id=evaluation_id,
        evaluatee_id=payload.evaluatee_id,
        evaluator_id=payload.evaluator_id,
        relationship=payload.relationship,
        weight=payload.weight,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get("/{evaluation_id}/assignments", response_model=list[AssignmentRead])
def list_assignments(
    evaluation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[EvaluatorAssignment]:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    return list(
        db.scalars(
            select(EvaluatorAssignment).where(
                EvaluatorAssignment.company_id == current_user.company_id,
                EvaluatorAssignment.evaluation_id == evaluation_id,
            )
        )
    )
