from uuid import UUID

from pydantic import BaseModel, Field


class SurveyTokenRead(BaseModel):
    assignment_id: UUID
    token: str
    public_url: str


class SurveyQuestion(BaseModel):
    id: UUID
    text: str
    competency: str


class PublicSurveyRead(BaseModel):
    evaluation_title: str
    evaluatee_name: str
    evaluator_name: str
    questions: list[SurveyQuestion]


class ResponseItem(BaseModel):
    question_id: UUID
    score: int = Field(ge=1, le=10)
    comment: str | None = None


class SubmitSurveyRequest(BaseModel):
    responses: list[ResponseItem] = Field(min_length=1)


class SubmitSurveyResponse(BaseModel):
    saved: int
