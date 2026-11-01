from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id"), index=True
    )
    s3_key: Mapped[str] = mapped_column(String(512))
    media_type: Mapped[str] = mapped_column(String(50))
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(Integer)
    captured_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    exif_removed: Mapped[bool] = mapped_column(Boolean, default=False)
    processing_status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    public_thumbnail_key: Mapped[str | None] = mapped_column(String(512), nullable=True)

    report: Mapped["Report | None"] = relationship(back_populates="media_assets")  # noqa: F821
    ai_analyses: Mapped[list["AIAnalysis"]] = relationship(  # noqa: F821
        back_populates="media_asset"
    )
    segmentation_assets: Mapped[list["SegmentationAsset"]] = relationship(  # noqa: F821
        back_populates="media_asset", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MediaAsset {self.id} type={self.media_type} status={self.processing_status}>"
