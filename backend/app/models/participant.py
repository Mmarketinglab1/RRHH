from datetime import datetime
from decimal import Decimal
from uuid import UUID as PyUUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Participant(Base):
    __tablename__ = "participants"
    __table_args__ = (UniqueConstraint("company_id", "evaluation_id", "email"),)

    id: Mapped[PyUUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[PyUUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    evaluation_id: Mapped[PyUUID] = mapped_column(ForeignKey("evaluations.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    role: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class EvaluatorAssignment(Base):
    __tablename__ = "evaluator_assignments"
    __table_args__ = (
        UniqueConstraint("company_id", "evaluation_id", "evaluatee_id", "evaluator_id"),
    )

    id: Mapped[PyUUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[PyUUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    evaluation_id: Mapped[PyUUID] = mapped_column(ForeignKey("evaluations.id"), nullable=False)
    evaluatee_id: Mapped[PyUUID] = mapped_column(ForeignKey("participants.id"), nullable=False)
    evaluator_id: Mapped[PyUUID] = mapped_column(ForeignKey("participants.id"), nullable=False)
    relationship: Mapped[str] = mapped_column(String(60), default="peer", nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("1.0"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
