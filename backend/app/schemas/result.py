from uuid import UUID

from pydantic import BaseModel


class CompetencyResult(BaseModel):
    competency_id: UUID
    competency_name: str
    average: float
    weighted_average: float
    median: float
    stddev: float
    responses: int


class ParticipantRanking(BaseModel):
    participant_id: UUID
    participant_name: str
    average: float
    rank: int


class QuestionResult(BaseModel):
    question_id: UUID
    question_text: str
    question_text_self: str | None = None
    question_text_evaluator: str | None = None
    tag_self: str | None = None
    tag_evaluator: str | None = None
    question_type: str
    is_evaluative: bool
    competency_name: str
    average: float | None = None
    median: float | None = None
    stddev: float | None = None
    responses_count: int
    distribution: dict[str, int]


class EvaluationResults(BaseModel):
    evaluation_id: UUID
    average: float
    median: float
    stddev: float
    competencies: list[CompetencyResult]
    ranking: list[ParticipantRanking]
    questions: list[QuestionResult] = []
