from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.evaluation import Evaluation
from app.schemas.auth import CurrentUser
from app.schemas.result import EvaluationResults
from app.services.results_service import calculate_evaluation_results

router = APIRouter()


@router.get("/{evaluation_id}/results", response_model=EvaluationResults)
def get_results(
    evaluation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EvaluationResults:
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation or evaluation.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return calculate_evaluation_results(db, current_user.company_id, evaluation_id)
