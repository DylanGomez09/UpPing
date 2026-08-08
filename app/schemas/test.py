from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress, model_validator


class PingTestCreate(BaseModel):
    target_ip: IPvAnyAddress
    avg_latency_ms: float = Field(ge=0)
    packets_sent: int = Field(ge=0)
    packets_received: int = Field(ge=0)
    loss_percent: float = Field(ge=0, le=100)
    ran_at: datetime

    @model_validator(mode="after")
    def _packets_consistent(self) -> "PingTestCreate":
        if self.packets_received > self.packets_sent:
            raise ValueError(
                "packets_received no puede ser mayor que packets_sent"
            )
        return self


class PingTestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    target_ip: str
    avg_latency_ms: float
    packets_sent: int
    packets_received: int
    loss_percent: float
    ran_at: datetime
    created_at: datetime


class PingTestList(BaseModel):
    items: list[PingTestOut]
    total: int
    limit: int
    offset: int
