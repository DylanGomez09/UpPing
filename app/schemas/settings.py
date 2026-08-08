from pydantic import BaseModel, ConfigDict, Field


class SettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ping_interval_ms: int
    timeout_ms: int
    auto_save_csv: bool
    performance_mode: bool


class SettingsUpdate(BaseModel):
    ping_interval_ms: int | None = Field(default=None, ge=100, le=60000)
    timeout_ms: int | None = Field(default=None, ge=100, le=60000)
    auto_save_csv: bool | None = None
    performance_mode: bool | None = None
