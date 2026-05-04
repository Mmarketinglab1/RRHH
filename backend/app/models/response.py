from datetime import datetime
from uuid import UUID as PyUUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class SurveyToken(Base):
    __tablename__ = "survey_tokens"

    id: Mapped[PyUUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[PyUUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    evaluation_id: Mapped[PyUUID] = mapped_column(ForeignKey("evaluations.id"), nullable=False)
    assignment_id: Mapped[PyUUID] = mapped_column(ForeignKey("evaluator_assignments.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Response(Base):
    __tablename__ = "responses"
    __table_args__ = (
        CheckConstraint("score BETWEEN 1 AND 10"),
        UniqueConstraint("company_id", "assignment_id", "question_id"),
    )

    id: Mapped[PyUUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[PyUUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    evaluation_id: Mapped[PyUUID] = mapped_column(ForeignKey("evaluations.id"), nullable=False)
    assignment_id: Mapped[PyUUID] = mapped_column(ForeignKey("evaluator_assignments.id"), nullable=False)
    question_id: Mapped[PyUUID] = mapped_column(ForeignKey("questions.id"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
