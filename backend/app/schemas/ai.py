from uuid import UUID

from pydantic import BaseModel


class GeneratedQuestion(BaseModel):
    competency_id: UUID
    text: str
    text_self: str | None = None
    text_evaluator: str | None = None


class GeneratedQuestionsResponse(BaseModel):
    questions: list[GeneratedQuestion]


class AIReportRead(BaseModel):
    report_type: str
    content: dict
