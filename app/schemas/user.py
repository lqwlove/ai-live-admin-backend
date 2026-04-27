from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    email: str = Field(min_length=3, max_length=255)
    role: str = "user"
    status: str = "active"


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=2, max_length=64)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    role: str | None = None
    status: str | None = None


class PasswordReset(BaseModel):
    password: str = Field(min_length=6, max_length=128)


class UserOut(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
