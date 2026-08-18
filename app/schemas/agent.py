from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# Dashboard Schemas
class DashboardStatsResponse(BaseModel):
    """Dashboard statistics response"""
    total_codes: int
    total_customers: int
    customers_change: float = Field(..., description="Percentage change in customers")
    completed_signups: int
    pending_verification: int
    in_progress: int
    efficiency_score: float
    
    model_config = ConfigDict(from_attributes=True)


# Referral Code Schemas

class ReferralCodeBase(BaseModel):
    """Base referral code schema"""
    code: str
    bank: str
    status: str = "active"
    expires_at: Optional[datetime] = None


class ReferralCodeCreate(BaseModel):
    """Create referral code schema"""
    bank: str = Field(..., description="Bank name")
    expires_at: Optional[datetime] = None


class ReferralCodeUpdate(BaseModel):
    """Update referral code schema"""
    status: Optional[str] = None
    bank: Optional[str] = None
    expires_at: Optional[datetime] = None


class ReferralCodeResponse(ReferralCodeBase):
    """Referral code response schema"""
    id: UUID
    agent_id: UUID
    customers_referred: int
    revenue_generated: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReferralCodeListResponse(BaseModel):
    codes: List[ReferralCodeResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# Rewards Schemas
class RewardsSummaryResponse(BaseModel):
    """Rewards overview response"""
    total_earned: float
    pending_rewards: float
    total_bonuses: float
    current_month_earnings: float
    previous_month_earnings: float
    growth_percentage: float
    
    model_config = ConfigDict(from_attributes=True)


class TransactionResponse(BaseModel):
    """Transaction response schema"""
    id: str
    transaction_id: str
    amount: float
    type: str
    status: str
    description: Optional[str]
    reward_id: Optional[str]
    customer_name: Optional[str]
    referral_code: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TransactionListResponse(BaseModel):
    """Transaction list response"""
    transactions: List[TransactionResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# Wallet Schemas
class WalletBalanceResponse(BaseModel):
    """Wallet balance response"""
    balance: float
    pending_balance: float
    total_earned: float
    total_withdrawn: float
    currency: str = "NGN"
    
    model_config = ConfigDict(from_attributes=True)


class PayoutMethodResponse(BaseModel):
    """Payout method response"""
    bank_name: str
    account_number: str
    account_name: str
    routing_number: Optional[str]
    is_verified: bool
    last_updated: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PayoutMethodUpdate(BaseModel):
    """Update payout method schema"""
    bank_name: str
    account_number: str
    account_name: str
    routing_number: Optional[str] = None


# Profile Schemas
class AgentProfileResponse(BaseModel):
    """Agent profile response"""
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    avatar: Optional[str]
    agent_code: str
    agent_tier: str
    region: Optional[str]
    status: str
    verification_status: bool
    efficiency_score: float
    referral_partner_id: Optional[str]
    created_at: datetime
    last_login_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class AgentProfileUpdate(BaseModel):
    """Update agent profile schema"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    region: Optional[str] = None
    avatar: Optional[str] = None


# Network Schemas
class NetworkStatsResponse(BaseModel):
    """Referral network statistics"""
    total_downline: int
    active_downline: int
    total_revenue_from_downline: float
    tier_breakdown: dict
    
    model_config = ConfigDict(from_attributes=True)