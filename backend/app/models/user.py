from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    display_name: Mapped[str] = mapped_column(String(255))
    auth_subject: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(50), default="public", index=True)
    organisation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    organisation: Mapped["Organisation | None"] = relationship(back_populates="users")  # noqa: F821

    def __repr__(self) -> str:
        return f"<User {self.email} role={self.role}>"
