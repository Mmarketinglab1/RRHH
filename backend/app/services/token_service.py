import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.evaluation import Evaluation
from app.models.participant import EvaluatorAssignment
from app.models.response import SurveyToken


def create_survey_token(db: Session, assignment: EvaluatorAssignment) -> SurveyToken:
    token = secrets.token_urlsafe(32)
    evaluation = db.get(Evaluation, assignment.evaluation_id)
    expires_at = (
        evaluation.ends_at
        if (evaluation and evaluation.ends_at)
        else (datetime.now(timezone.utc) + timedelta(days=30))
    )
    survey_token = SurveyToken(
        company_id=assignment.company_id,
        evaluation_id=assignment.evaluation_id,
        assignment_id=assignment.id,
        token=token,
        expires_at=expires_at,
    )
    db.add(survey_token)
    db.commit()
    db.refresh(survey_token)
    return survey_token
