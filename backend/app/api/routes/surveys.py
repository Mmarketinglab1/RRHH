from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.evaluation import Competency, Evaluation, Question
from app.models.participant import EvaluatorAssignment, Participant
from app.models.response import Response, SurveyToken
from app.schemas.auth import CurrentUser
from app.schemas.survey import PublicSurveyRead, SubmitSurveyRequest, SubmitSurveyResponse, SurveyQuestion, SurveyTokenRead
from app.services.token_service import create_survey_token

router = APIRouter()


@router.post("/assignments/{assignment_id}/token", response_model=SurveyTokenRead)
def generate_assignment_token(
    assignment_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SurveyTokenRead:
    assignment = db.get(EvaluatorAssignment, assignment_id)
    if not assignment or assignment.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Assignment not found")

    survey_token = create_survey_token(db, assignment)
    return SurveyTokenRead(
        assignment_id=assignment.id,
        token=survey_token.token,
        public_url=f"/surveys/public/{survey_token.token}",
    )


@router.get("/public/{token}", response_model=PublicSurveyRead)
def get_public_survey(token: str, db: Session = Depends(get_db)) -> PublicSurveyRead:
    survey_token = db.scalar(select(SurveyToken).where(SurveyToken.token == token))
    if not survey_token:
        raise HTTPException(status_code=404, detail="Survey not found")
    if survey_token.expires_at and survey_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Survey expired")

    assignment = db.get(EvaluatorAssignment, survey_token.assignment_id)
    evaluation = db.get(Evaluation, survey_token.evaluation_id)
    evaluatee = db.get(Participant, assignment.evaluatee_id)
    evaluator = db.get(Participant, assignment.evaluator_id)

    questions = db.execute(
        select(Question, Competency)
        .join(Competency, Competency.id == Question.competency_id)
        .where(
            Question.company_id == survey_token.company_id,
            Question.evaluation_id == survey_token.evaluation_id,
        )
        .order_by(Question.position.asc())
    ).all()

    return PublicSurveyRead(
        evaluation_title=evaluation.title,
        evaluatee_name=evaluatee.full_name,
        evaluator_name=evaluator.full_name,
        questions=[
            SurveyQuestion(id=question.id, text=question.text, competency=competency.name)
            for question, competency in questions
        ],
    )


@router.post("/public/{token}/responses", response_model=SubmitSurveyResponse)
def submit_public_survey(
    token: str,
    payload: SubmitSurveyRequest,
    db: Session = Depends(get_db),
) -> SubmitSurveyResponse:
    survey_token = db.scalar(select(SurveyToken).where(SurveyToken.token == token))
    if not survey_token:
        raise HTTPException(status_code=404, detail="Survey not found")
    if survey_token.expires_at and survey_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Survey expired")

    valid_questions = set(
        db.scalars(
            select(Question.id).where(
                Question.company_id == survey_token.company_id,
                Question.evaluation_id == survey_token.evaluation_id,
            )
        )
    )
    saved = 0
    for item in payload.responses:
        if item.question_id not in valid_questions:
            raise HTTPException(status_code=400, detail="Question does not belong to survey")

        existing = db.scalar(
            select(Response).where(
                Response.company_id == survey_token.company_id,
                Response.assignment_id == survey_token.assignment_id,
                Response.question_id == item.question_id,
            )
        )
        if existing:
            existing.score = item.score
            existing.comment = item.comment
        else:
            db.add(
                Response(
                    company_id=survey_token.company_id,
                    evaluation_id=survey_token.evaluation_id,
                    assignment_id=survey_token.assignment_id,
                    question_id=item.question_id,
                    score=item.score,
                    comment=item.comment,
                )
            )
        saved += 1

    survey_token.used_at = datetime.now(timezone.utc)
    db.commit()
    return SubmitSurveyResponse(saved=saved)
