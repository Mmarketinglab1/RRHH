from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class EvaluationCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class EvaluationRead(BaseModel):
    id: UUID
    title: str
    description: str | None
    status: str
    starts_at: datetime | None
    ends_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CompetencyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str | None = None
    weight: Decimal = Field(default=Decimal("1.0"), gt=0)


class CompetencyRead(BaseModel):
    id: UUID
    evaluation_id: UUID
    name: str
    description: str | None
    weight: Decimal

    model_config = {"from_attributes": True}


class QuestionCreate(BaseModel):
    competency_id: UUID
    text: str = Field(min_length=5)
    position: int = 0


class QuestionRead(BaseModel):
    id: UUID
    evaluation_id: UUID
    competency_id: UUID
    text: str
    position: int

    model_config = {"from_attributes": True}
