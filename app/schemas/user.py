from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.user import UserRole, AgentTier, UserStatus


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: Optional[UserRole] = UserRole.AGENT
    agent_tier: Optional[AgentTier] = None
    region: Optional[str] = Field(None, max_length=100)
    agent_code: Optional[str] = Field(None, max_length=50)


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8)
    status: Optional[UserStatus] = UserStatus.PENDING


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    status: Optional[UserStatus] = None
    agent_tier: Optional[AgentTier] = None
    region: Optional[str] = Field(None, max_length=100)
    agent_code: Optional[str] = Field(None, max_length=50)
    password: Optional[str] = Field(None, min_length=8)
    avatar: Optional[str] = None
    efficiency_score: Optional[float] = Field(None, ge=0, le=100)


class UserInDB(UserBase):
    """Schema for user stored in database"""
    id: str
    status: UserStatus
    avatar: Optional[str]
    verification_status: bool
    efficiency_score: float
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserInDB):
    """Schema for user API response"""
    pass


class AgentProfileResponse(BaseModel):
    """Schema for agent profile response"""
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    avatar: Optional[str]
    agent_code: Optional[str]
    agent_tier: Optional[str]
    region: Optional[str]
    status: str
    verification_status: bool
    efficiency_score: float
    created_at: datetime
    last_login_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class AgentListResponse(BaseModel):
    """Schema for agent list response"""
    id: str
    email: str
    first_name: str
    last_name: str
    agent_code: Optional[str]
    agent_tier: Optional[str]
    region: Optional[str]
    status: str
    customers_count: Optional[int] = 0
    rewards_earned: Optional[float] = 0.0
    efficiency_score: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminProfileResponse(BaseModel):
    """Schema for admin profile response"""
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    admin_level: Optional[str]
    permissions: list
    created_at: datetime
    last_login_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)