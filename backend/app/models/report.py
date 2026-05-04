from datetime import datetime
from uuid import UUID as PyUUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AIReport(Base):
    __tablename__ = "ai_reports"

    id: Mapped[PyUUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[PyUUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    evaluation_id: Mapped[PyUUID] = mapped_column(ForeignKey("evaluations.id"), nullable=False)
    participant_id: Mapped[PyUUID | None] = mapped_column(ForeignKey("participants.id"))
    report_type: Mapped[str] = mapped_column(String(40), nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
