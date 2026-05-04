from datetime import datetime
from decimal import Decimal
from uuid import UUID as PyUUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[PyUUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[PyUUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[PyUUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    competencies = relationship("Competency", cascade="all, delete-orphan")
    questions = relationship("Question", cascade="all, delete-orphan")


class Competency(Base):
    __tablename__ = "competencies"

    id: Mapped[PyUUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[PyUUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    evaluation_id: Mapped[PyUUID] = mapped_column(ForeignKey("evaluations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    weight: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("1.0"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    questions = relationship("Question", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[PyUUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[PyUUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    evaluation_id: Mapped[PyUUID] = mapped_column(ForeignKey("evaluations.id"), nullable=False)
    competency_id: Mapped[PyUUID] = mapped_column(ForeignKey("competencies.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
