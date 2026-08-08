from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import LicenseTier


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    display_name: str
    license_tier: LicenseTier
    created_at: datetime


class MeOut(UserOut):
    total_tests: int


class UpdateProfileRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)
