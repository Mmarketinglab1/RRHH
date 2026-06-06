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
    question_type: str
    options: list | dict | None = None
    is_evaluative: bool


class PublicSurveyRead(BaseModel):
    evaluation_title: str
    evaluatee_name: str
    evaluator_name: str
    relationship: str
    questions: list[SurveyQuestion]


class ResponseItem(BaseModel):
    question_id: UUID
    score: int | None = Field(default=None, ge=0, le=10)
    selected_option: str | None = None
    selected_options: list[str] | None = None
    comment: str | None = None


class SubmitSurveyRequest(BaseModel):
    responses: list[ResponseItem] = Field(min_length=1)


class SubmitSurveyResponse(BaseModel):
    saved: int
