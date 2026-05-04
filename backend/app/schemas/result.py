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


class EvaluationResults(BaseModel):
    evaluation_id: UUID
    average: float
    median: float
    stddev: float
    competencies: list[CompetencyResult]
    ranking: list[ParticipantRanking]
