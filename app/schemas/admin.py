from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID




class AdminDashboardStatsResponse(BaseModel):
    """Platform-wide overview statistics for the admin dashboard"""
    total_agents: int
    active_agents: int
    pending_agents: int
    total_customers: int
    total_referral_codes: int
    active_referral_codes: int
    pending_rewards_count: int
    pending_rewards_amount: float
    pending_payments_count: int
    pending_payments_amount: float
    total_revenue: float
    total_paid_out: float

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Agent management
# ---------------------------------------------------------------------------

class AdminAgentListItem(BaseModel):
    """Row shape for the Agents list screen"""
    id: UUID
    email: str
    first_name: str
    last_name: str
    agent_code: Optional[str]
    agent_tier: Optional[str]
    region: Optional[str]
    status: str
    efficiency_score: float
    customers_count: int = 0
    total_earned: float = 0.0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminAgentListResponse(BaseModel):
    agents: List[AdminAgentListItem]
    total: int
    page: int
    limit: int
    total_pages: int


class AdminAgentDetailResponse(BaseModel):
    """Full agent detail shown when an admin opens a single agent"""
    id: UUID
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
    referral_partner_id: Optional[UUID]
    payout_method_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class AdminAgentCreate(BaseModel):
    """Admin-initiated agent creation (e.g. onboarding on an agent's behalf)"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    agent_tier: Optional[str] = None
    region: Optional[str] = Field(None, max_length=100)


class AdminAgentUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    agent_tier: Optional[str] = None
    region: Optional[str] = Field(None, max_length=100)


class AdminAgentStatusUpdate(BaseModel):
    """Suspend / reactivate an agent"""
    status: str = Field(..., description="active | suspended | pending")
    reason: Optional[str] = Field(None, max_length=500)


# ---------------------------------------------------------------------------
# Referral codes (admin, cross-agent view)
# ---------------------------------------------------------------------------

class AdminReferralCodeListItem(BaseModel):
    id: UUID
    code: str
    agent_id: UUID
    agent_name: str
    bank: str
    status: str
    customers_referred: int
    revenue_generated: float
    expires_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminReferralCodeListResponse(BaseModel):
    codes: List[AdminReferralCodeListItem]
    total: int
    page: int
    limit: int
    total_pages: int


class AdminReferralCodeStatusUpdate(BaseModel):
    status: str = Field(..., description="active | inactive | expired")


# ---------------------------------------------------------------------------
# Rewards (reward transactions) — "Rewards Management" screen
# ---------------------------------------------------------------------------

class AdminRewardListItem(BaseModel):
    id: UUID
    reward_id: str = Field(..., description="e.g. RW-98210 (Transaction.transaction_id)")
    agent_id: UUID
    agent_name: str
    referral_code: Optional[str]
    customer_id: Optional[UUID]
    amount: float
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminRewardListResponse(BaseModel):
    rewards: List[AdminRewardListItem]
    total: int
    page: int
    limit: int
    total_pages: int


class AdminRewardDecision(BaseModel):
    """Body for approve/reject actions on a pending reward"""
    reason: Optional[str] = Field(None, max_length=500)


# ---------------------------------------------------------------------------
# Payments — "Payments Tracking" screen
# ---------------------------------------------------------------------------

class AdminPaymentListItem(BaseModel):
    id: UUID
    payment_id: str = Field(..., description="e.g. PAY-982103")
    agent_id: UUID
    agent_name: str
    amount: float
    payment_date: datetime
    status: str
    bank_name: Optional[str]
    transaction_reference: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class AdminPaymentListResponse(BaseModel):
    payments: List[AdminPaymentListItem]
    total: int
    page: int
    limit: int
    total_pages: int


class AdminPaymentBatchCreate(BaseModel):
    """Create a payment batch ('Create Payment Batch' action) for one or more agents"""
    agent_ids: List[UUID] = Field(..., min_length=1)
    payment_date: Optional[datetime] = None
    note: Optional[str] = Field(None, max_length=500)


class AdminPaymentBatchResponse(BaseModel):
    batch_id: str
    payments_created: int
    total_amount: float
    payments: List[AdminPaymentListItem]


class AdminPaymentProcess(BaseModel):
    """Advance a payment through its lifecycle ('Process Payment' action)"""
    status: str = Field(..., description="processing | paid | failed")
    transaction_reference: Optional[str] = Field(None, max_length=100)


# ---------------------------------------------------------------------------
# Reports — "Reports & Analytics" screen
# ---------------------------------------------------------------------------

class AgentPerformanceItem(BaseModel):
    agent_id: UUID
    agent_name: str
    agent_code: Optional[str]
    region: Optional[str]
    referrals: int
    revenue: float
    commission: float
    status: str

    model_config = ConfigDict(from_attributes=True)


class AgentPerformanceReportResponse(BaseModel):
    agents: List[AgentPerformanceItem]
    total: int
    page: int
    limit: int
    total_pages: int
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Settings — "Platform Settings" screen
# ---------------------------------------------------------------------------

class SystemSettingResponse(BaseModel):
    key: str
    value: Any
    category: Optional[str]
    description: Optional[str]
    is_public: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SystemSettingUpdate(BaseModel):
    value: Any


class PlatformSettingsResponse(BaseModel):
    """Convenience shape mirroring the 'Referral Program Settings' card"""
    reward_per_referral: float
    minimum_withdrawal: float


class PlatformSettingsUpdate(BaseModel):
    reward_per_referral: Optional[float] = Field(None, ge=0)
    minimum_withdrawal: Optional[float] = Field(None, ge=0)
