from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ModerationAction(Base):
    __tablename__ = "moderation_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id"), index=True
    )
    moderator_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(100))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_status: Mapped[str] = mapped_column(String(50))
    new_status: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    report: Mapped["Report | None"] = relationship(back_populates="moderation_actions")  # noqa: F821

    def __repr__(self) -> str:
        return f"<ModerationAction {self.action} report={self.report_id}>"
