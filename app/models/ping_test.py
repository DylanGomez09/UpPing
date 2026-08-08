from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PingTest(Base):
    __tablename__ = "ping_tests"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    target_ip: Mapped[str] = mapped_column(String(45), index=True, nullable=False)
    avg_latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    packets_sent: Mapped[int] = mapped_column(Integer, nullable=False)
    packets_received: Mapped[int] = mapped_column(Integer, nullable=False)
    loss_percent: Mapped[float] = mapped_column(Float, nullable=False)
    ran_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="ping_tests")
