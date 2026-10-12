from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class EvaluationCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str | None = None
    assessment_type: str | None = Field(default="individual_contributor", max_length=60)
    client_logo_url: str | None = None
    consultant_logo_url: str | None = None
    scale_type: str | None = Field(default="numeric_1_10", max_length=50)
    score_thresholds: dict | None = None
    report_config: dict | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class EvaluationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    status: str | None = Field(default=None, max_length=40)
    assessment_type: str | None = Field(default=None, max_length=60)
    client_logo_url: str | None = None
    consultant_logo_url: str | None = None
    scale_type: str | None = Field(default=None, max_length=50)
    score_thresholds: dict | None = None
    report_config: dict | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class EvaluationRead(BaseModel):
    id: UUID
    title: str
    description: str | None
    status: str
    assessment_type: str | None = "individual_contributor"
    client_logo_url: str | None = None
    consultant_logo_url: str | None = None
    scale_type: str | None = "numeric_1_10"
    score_thresholds: dict | None = None
    report_config: dict | None = None
    starts_at: datetime | None
    ends_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CompetencyBankCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None


class CompetencyBankUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None


class CompetencyBankRead(BaseModel):
    id: UUID
    name: str
    description: str | None
    company_id: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CompetencyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str | None = None
    weight: Decimal = Field(default=Decimal("1.0"), gt=0)
    competency_bank_id: UUID | None = None


class CompetencyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = None
    weight: Decimal | None = Field(default=None, gt=0)
    competency_bank_id: UUID | None = None


class CompetencyRead(BaseModel):
    id: UUID
    evaluation_id: UUID
    competency_bank_id: UUID | None = None
    name: str
    description: str | None
    weight: Decimal

    model_config = {"from_attributes": True}


class QuestionCreate(BaseModel):
    competency_id: UUID
    text: str = Field(min_length=5)
    text_self: str | None = None
    text_evaluator: str | None = None
    tag_self: str | None = None
    tag_evaluator: str | None = None
    position: int = 0
    question_type: str = "numeric_1_10"
    options: list | dict | None = None
    is_evaluative: bool = True
    save_to_bank: bool = False


class QuestionUpdate(BaseModel):
    competency_id: UUID | None = None
    text: str | None = Field(default=None, min_length=5)
    text_self: str | None = None
    text_evaluator: str | None = None
    tag_self: str | None = None
    tag_evaluator: str | None = None
    position: int | None = None
    question_type: str | None = None
    options: list | dict | None = None
    is_evaluative: bool | None = None


class QuestionRead(BaseModel):
    id: UUID
    evaluation_id: UUID
    competency_id: UUID
    text: str
    text_self: str | None = None
    text_evaluator: str | None = None
    tag_self: str | None = None
    tag_evaluator: str | None = None
    position: int
    question_type: str
    options: list | dict | None
    is_evaluative: bool

    model_config = {"from_attributes": True}


class QuestionBankRead(BaseModel):
    id: UUID
    company_id: UUID | None
    competency_bank_id: UUID | None = None
    competency_name: str
    text: str
    text_self: str | None = None
    text_evaluator: str | None = None
    tag_self: str | None = None
    tag_evaluator: str | None = None
    question_type: str
    options: list | dict | None
    is_evaluative: bool

    model_config = {"from_attributes": True}
