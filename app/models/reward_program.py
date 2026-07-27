from sqlalchemy import Column, String, Float, DateTime, Boolean, Enum, Integer
from app.models.base import BaseModel
import enum


class RewardProgramStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"


class RewardProgram(BaseModel):
    __tablename__ = "reward_programs"

    name = Column(String(255), nullable=False)
    description = Column(String(1000))
    commission_rate = Column(Float, nullable=False)
    minimum_referrals = Column(Integer, default=1)
    reward_per_referral = Column(Float, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(RewardProgramStatus), default=RewardProgramStatus.ACTIVE)
    is_default = Column(Boolean, default=False)