from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    status: str
    agent_code: Optional[str]
    agent_tier: Optional[str]
    avatar: Optional[str]
    region: Optional[str]
    efficiency_score: Optional[float]
    created_at: datetime
    last_login_at: Optional[datetime]