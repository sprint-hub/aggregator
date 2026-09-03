from sqlalchemy import Column, String, Boolean, DateTime, Enum, JSON, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.models.base import BaseModel
import enum


class UserRole(str, enum.Enum):
    AGENT = "agent"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"


class AgentTier(str, enum.Enum):
    INDIVIDUAL = "individual"
    CORPORATE = "corporate"
    ELITE = "elite"
    SENIOR_PARTNER = "senior_partner"


class User(BaseModel):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    avatar = Column(String(500))

    role = Column(Enum(UserRole), nullable=False, default=UserRole.AGENT)
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.PENDING)

    # Agent specific fields
    agent_code = Column(String(50), unique=True, index=True)
    agent_tier = Column(Enum(AgentTier), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    region = Column(String(100))
    referral_partner_id = Column(UUID(as_uuid=True), nullable=True)  # For downline
    efficiency_score = Column(Float, default=0.0)
    verification_status = Column(Boolean, default=False)

    # Payout
    default_bank_name = Column(String(100), nullable=True)
    bank_account_last4 = Column(String(4), nullable=True)
    bank_account_encrypted = Column(String(500), nullable=True)  # Encrypted full account
    routing_number = Column(String(20), nullable=True)
    payout_method_verified = Column(Boolean, default=False)
    payout_verified_at = Column(DateTime(timezone=True), nullable=True)

    # Admin specific fields
    admin_level = Column(String(50), nullable=True)
    permissions = Column(JSON, default=list)

    # Timestamps
    last_login_at = Column(DateTime(timezone=True))
    last_login_ip = Column(String(45))

