from sqlalchemy import Column, String, Boolean, DateTime, Enum, Integer, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.user import User
import enum


class ReferralCodeStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"


class ReferralCode(BaseModel):
    __tablename__ = "referral_codes"

    code = Column(String(50), unique=True, index=True, nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    bank = Column(String(100), nullable=False)
    status = Column(Enum(ReferralCodeStatus), default=ReferralCodeStatus.ACTIVE)
    customers_referred = Column(Integer, default=0)
    revenue_generated = Column(Float, default=0.0)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    agent = relationship("User", backref="referral_codes")
    customers = relationship("Customer", back_populates="referral_code")


class CustomerStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    PREMIUM = "premium"
    KYC_IN_PROGRESS = "kyc_in_progress"
    REWARD_ELIGIBLE = "reward_eligible"


class Customer(BaseModel):
    __tablename__ = "customers"

    name = Column(String(255), nullable=False)
    email = Column(String(255), index=True)
    phone = Column(String(20))
    agent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    referral_code_id = Column(UUID(as_uuid=True), ForeignKey("referral_codes.id"), nullable=False)
    status = Column(Enum(CustomerStatus), default=CustomerStatus.PENDING)
    initial_deposit = Column(Float, default=0.0)
    metadata = Column(JSON, default=dict)

    # Relationships
    agent = relationship("User", backref="customers")
    referral_code = relationship("ReferralCode", back_populates="customers")
    transactions = relationship("Transaction", back_populates="customer")