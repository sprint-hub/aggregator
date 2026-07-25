from sqlalchemy import Column, String, Float, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class TransactionType(str, enum.Enum):
    CREDIT = "credit"
    DEBIT = "debit"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


class Transaction(BaseModel):
    __tablename__ = "transactions"

    transaction_id = Column(String(50), unique=True, index=True, nullable=False)  # RW-98421 format
    agent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    referral_code_id = Column(UUID(as_uuid=True), ForeignKey("referral_codes.id"), nullable=True)

    type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    description = Column(String(500))

    # Reward specific
    reward_id = Column(String(50), nullable=True)  # Reference to reward program
    commission_rate = Column(Float, default=0.0)

    # Payment specific
    payment_id = Column(String(50), nullable=True)
    payment_method = Column(String(100))

    # Relationships
    agent = relationship("User", backref="transactions")
    customer = relationship("Customer", back_populates="transactions")