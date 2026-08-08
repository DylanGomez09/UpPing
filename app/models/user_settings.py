from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    ping_interval_ms: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    timeout_ms: Mapped[int] = mapped_column(Integer, default=1500, nullable=False)
    auto_save_csv: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    performance_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship(back_populates="settings")
