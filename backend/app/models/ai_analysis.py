from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id"), index=True
    )
    media_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_assets.id"), index=True
    )
    provider: Mapped[str] = mapped_column(String(100), index=True)
    model_id: Mapped[str] = mapped_column(String(100))
    model_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    scene_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    structured_result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    limitations: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    processing_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    report: Mapped["Report | None"] = relationship(back_populates="ai_analyses")  # noqa: F821
    media_asset: Mapped["MediaAsset | None"] = relationship(back_populates="ai_analyses")  # noqa: F821

    def __repr__(self) -> str:
        return f"<AIAnalysis {self.id} provider={self.provider} model={self.model_id} status={self.status}>"
