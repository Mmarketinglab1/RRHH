import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.participant import EvaluatorAssignment
from app.models.response import SurveyToken


def create_survey_token(db: Session, assignment: EvaluatorAssignment) -> SurveyToken:
    token = secrets.token_urlsafe(32)
    survey_token = SurveyToken(
        company_id=assignment.company_id,
        evaluation_id=assignment.evaluation_id,
        assignment_id=assignment.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(survey_token)
    db.commit()
    db.refresh(survey_token)
    return survey_token
