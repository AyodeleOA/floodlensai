from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RiskCell(Base):
    __tablename__ = "risk_cells"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    grid_system: Mapped[str] = mapped_column(String(50), default="h3", index=True)
    grid_index: Mapped[str] = mapped_column(String(255), index=True)
    geometry_wkt: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, index=True)
    longitude: Mapped[float] = mapped_column(Float, index=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    risk_band: Mapped[str] = mapped_column(String(50), default="low", index=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    data_completeness: Mapped[float] = mapped_column(Float, default=0.0)
    contributing_factors: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    missing_inputs: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    source_ids: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    calculation_version: Mapped[str] = mapped_column(String(50), default="0.1.0")
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_illustrative: Mapped[bool] = mapped_column(Boolean, default=False)

    evidence: Mapped[list["RiskCellEvidence"]] = relationship(  # noqa: F821
        back_populates="risk_cell", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<RiskCell {self.grid_index} score={self.risk_score} band={self.risk_band}>"
