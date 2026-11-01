from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SegmentationAsset(Base):
    __tablename__ = "segmentation_assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    media_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_assets.id"), index=True
    )
    provider: Mapped[str] = mapped_column(String(100), index=True)
    model_id: Mapped[str] = mapped_column(String(100))
    prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    mask_s3_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    bounding_boxes: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    object_labels: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    media_asset: Mapped["MediaAsset | None"] = relationship(  # noqa: F821
        back_populates="segmentation_assets"
    )

    def __repr__(self) -> str:
        return f"<SegmentationAsset {self.id} provider={self.provider} model={self.model_id}>"
