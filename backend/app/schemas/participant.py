from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class ParticipantCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=160)
    role: str | None = Field(default=None, max_length=120)
    business_line: str | None = Field(default=None, max_length=120)
    performance_history: dict[str, str] = Field(default_factory=dict)


class ParticipantUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=2, max_length=160)
    role: str | None = Field(default=None, max_length=120)
    business_line: str | None = Field(default=None, max_length=120)
    performance_history: dict[str, str] | None = None


class ParticipantRead(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: str | None
    business_line: str | None = None
    performance_history: dict[str, str] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class CSVUploadResult(BaseModel):
    created: int
    skipped: int


class AssignmentCreate(BaseModel):
    evaluatee_id: UUID
    evaluator_id: UUID
    relationship: str = Field(default="peer", max_length=60)
    weight: Decimal = Field(default=Decimal("1.0"), gt=0)


class AssignmentRead(BaseModel):
    id: UUID
    evaluation_id: UUID
    evaluatee_id: UUID
    evaluator_id: UUID
    relationship: str
    weight: Decimal
    is_completed: bool = False
    survey_token: str | None = None

    model_config = {"from_attributes": True}
