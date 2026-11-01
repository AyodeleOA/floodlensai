from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EnvironmentalObservation(Base):
    __tablename__ = "environmental_observations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("data_sources.id"), index=True
    )
    observation_type: Mapped[str] = mapped_column(String(100), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality_flag: Mapped[str | None] = mapped_column(String(50), nullable=True)
    raw_s3_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    geometry_wkt: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    source: Mapped["DataSource | None"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<EnvironmentalObservation {self.id} type={self.observation_type}>"


class RiskCellEvidence(Base):
    __tablename__ = "risk_cell_evidence"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    risk_cell_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("risk_cells.id"), index=True
    )
    evidence_type: Mapped[str] = mapped_column(String(100))
    evidence_id: Mapped[str] = mapped_column(String(255))
    contribution: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    risk_cell: Mapped["RiskCell | None"] = relationship(back_populates="evidence")  # noqa: F821

    def __repr__(self) -> str:
        return f"<RiskCellEvidence {self.id} type={self.evidence_type}>"
