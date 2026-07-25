from sqlalchemy import Column, String, Float, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class PaymentStatus(str, enum.Enum):
    PAID = "paid"
    PROCESSING = "processing"
    PENDING = "pending"
    FAILED = "failed"


class Payment(BaseModel):
    __tablename__ = "payments"

    payment_id = Column(String(50), unique=True, index=True, nullable=False)  # PAY-982103
    agent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)

    bank_name = Column(String(100))
    bank_account = Column(String(50))
    transaction_reference = Column(String(100))

    # Relationships
    agent = relationship("User", backref="payments")