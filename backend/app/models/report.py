from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    reporter_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    organisation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=True
    )
    report_type: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float] = mapped_column(Float, index=True)
    longitude: Mapped[float] = mapped_column(Float, index=True)
    reported_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    status: Mapped[str] = mapped_column(String(50), default="submitted", index=True)
    source_channel: Mapped[str] = mapped_column(String(50), default="web")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False)
    duplicate_of_report_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    hazard_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    severity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    landmark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    water_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    affects_roads: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    affects_homes: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    affects_shops: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    affects_facilities: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    reporter_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    privacy_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    voice_transcript: Mapped[str | None] = mapped_column(Text, nullable=True)

    reporter: Mapped["User | None"] = relationship(  # noqa: F821
        foreign_keys=[reporter_user_id]
    )
    organisation: Mapped["Organisation | None"] = relationship(back_populates="reports")  # noqa: F821
    media_assets: Mapped[list["MediaAsset"]] = relationship(  # noqa: F821
        back_populates="report", cascade="all, delete-orphan"
    )
    ai_analyses: Mapped[list["AIAnalysis"]] = relationship(  # noqa: F821
        back_populates="report", cascade="all, delete-orphan"
    )
    moderation_actions: Mapped[list["ModerationAction"]] = relationship(  # noqa: F821
        back_populates="report"
    )

    def __repr__(self) -> str:
        return f"<Report {self.id} type={self.report_type} status={self.status}>"
