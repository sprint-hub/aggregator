from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload
from uuid import UUID
import uuid
from datetime import datetime, timedelta, timezone

from app.models.user import User
from app.models.referral import ReferralCode, ReferralCodeStatus, Customer, CustomerStatus
from app.models.transaction import Transaction, TransactionStatus, TransactionType
from app.models.payment import Payment, PaymentStatus
from app.schemas.agent import (
    ReferralCodeCreate,
    ReferralCodeUpdate,
    PayoutMethodUpdate,
    AgentProfileUpdate
)


class AgentService:
    """Service for agent-specific operations"""
    
    # Dashboard
    async def get_dashboard_stats(self, db: AsyncSession, agent_id: UUID) -> Dict[str, Any]:
        """Get agent dashboard statistics"""
        # Get total codes
        codes_query = select(func.count()).where(
            ReferralCode.agent_id == agent_id,
            ReferralCode.status == ReferralCodeStatus.ACTIVE
        )
        total_codes = await db.execute(codes_query)
        
        # Get total customers
        customers_query = select(func.count()).where(
            Customer.agent_id == agent_id
        )
        total_customers = await db.execute(customers_query)
        total_customers_count = total_customers.scalar() or 0
        
        # Get customer status breakdown
        completed_query = select(func.count()).where(
            Customer.agent_id == agent_id,
            Customer.status.in_([CustomerStatus.ACTIVE, CustomerStatus.PREMIUM])
        )
        completed = await db.execute(completed_query)
        
        pending_query = select(func.count()).where(
            Customer.agent_id == agent_id,
            Customer.status == CustomerStatus.PENDING
        )
        pending = await db.execute(pending_query)
        
        in_progress_query = select(func.count()).where(
            Customer.agent_id == agent_id,
            Customer.status == CustomerStatus.KYC_IN_PROGRESS
        )
        in_progress = await db.execute(in_progress_query)
        
        # Get efficiency score
        agent_query = select(User).where(User.id == agent_id)
        agent_result = await db.execute(agent_query)
        agent = agent_result.scalar_one_or_none()
        
        return {
            "total_codes": total_codes.scalar() or 0,
            "total_customers": total_customers_count,
            "customers_change": 5.4,  # TODO: Calculate from previous period
            "completed_signups": completed.scalar() or 0,
            "pending_verification": pending.scalar() or 0,
            "in_progress": in_progress.scalar() or 0,
            "efficiency_score": agent.efficiency_score if agent else 0.0
        }
    
    # Referral Codes
    async def get_codes(
        self,
        db: AsyncSession,
        agent_id: UUID,
        skip: int = 0,
        limit: int = 10,
        status: Optional[str] = None
    ) -> tuple[List[ReferralCode], int]:
        """Get agent's referral codes"""
        query = select(ReferralCode).where(ReferralCode.agent_id == agent_id)
        
        if status:
            query = query.where(ReferralCode.status == status)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.execute(count_query)
        total_count = total.scalar()
        
        # Get paginated results
        query = query.order_by(desc(ReferralCode.created_at)).offset(skip).limit(limit)
        result = await db.execute(query)
        codes = result.scalars().all()
        
        return codes, total_count
    
    async def create_code(
        self,
        db: AsyncSession,
        agent_id: UUID,
        code_data: ReferralCodeCreate
    ) -> ReferralCode:
        """Create a new referral code"""
        # Generate unique code
        code_prefix = code_data.bank[:3].upper()
        unique_id = uuid.uuid4().hex[:6].upper()
        code = f"{code_prefix}-{unique_id}"
        
        referral_code = ReferralCode(
            code=code,
            agent_id=agent_id,
            bank=code_data.bank,
            status=ReferralCodeStatus.ACTIVE,
            expires_at=code_data.expires_at
        )
        
        db.add(referral_code)
        await db.commit()
        await db.refresh(referral_code)
        return referral_code
    
    async def get_code(
        self,
        db: AsyncSession,
        code_id: UUID,
        agent_id: UUID
    ) -> Optional[ReferralCode]:
        """Get a specific referral code"""
        query = select(ReferralCode).where(
            ReferralCode.id == code_id,
            ReferralCode.agent_id == agent_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_code(
        self,
        db: AsyncSession,
        code_id: UUID,
        agent_id: UUID,
        code_data: ReferralCodeUpdate
    ) -> Optional[ReferralCode]:
        """Update a referral code"""
        code = await self.get_code(db, code_id, agent_id)
        if not code:
            return None
        
        update_data = code_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(code, key, value)
        
        await db.commit()
        await db.refresh(code)
        return code
    
    async def delete_code(
        self,
        db: AsyncSession,
        code_id: UUID,
        agent_id: UUID
    ) -> bool:
        """Delete a referral code"""
        code = await self.get_code(db, code_id, agent_id)
        if not code:
            return False
        
        # Soft delete - set status to inactive
        code.status = ReferralCodeStatus.INACTIVE
        await db.commit()
        return True
    
    # Rewards
    async def get_rewards_summary(self, db: AsyncSession, agent_id: UUID) -> Dict[str, Any]:
        """Get rewards overview"""
        # Get total earned
        earned_query = select(func.sum(Transaction.amount)).where(
            Transaction.agent_id == agent_id,
            Transaction.status == TransactionStatus.APPROVED,
            Transaction.type == TransactionType.CREDIT
        )
        total_earned = await db.execute(earned_query)
        
        # Get pending rewards
        pending_query = select(func.sum(Transaction.amount)).where(
            Transaction.agent_id == agent_id,
            Transaction.status == TransactionStatus.PENDING,
            Transaction.type == TransactionType.CREDIT
        )
        pending_rewards = await db.execute(pending_query)
        
        # Get current month earnings
        now = datetime.now(timezone.utc)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        current_month_query = select(func.sum(Transaction.amount)).where(
            Transaction.agent_id == agent_id,
            Transaction.status == TransactionStatus.APPROVED,
            Transaction.type == TransactionType.CREDIT,
            Transaction.created_at >= start_of_month
        )
        current_month = await db.execute(current_month_query)
        
        # Get previous month earnings
        start_of_prev_month = (start_of_month - timedelta(days=1)).replace(day=1)
        end_of_prev_month = start_of_month - timedelta(microseconds=1)
        
        prev_month_query = select(func.sum(Transaction.amount)).where(
            Transaction.agent_id == agent_id,
            Transaction.status == TransactionStatus.APPROVED,
            Transaction.type == TransactionType.CREDIT,
            Transaction.created_at >= start_of_prev_month,
            Transaction.created_at <= end_of_prev_month
        )
        prev_month = await db.execute(prev_month_query)
        
        current_month_value = current_month.scalar() or 0
        prev_month_value = prev_month.scalar() or 0
        
        # Calculate growth
        growth = 0
        if prev_month_value > 0:
            growth = ((current_month_value - prev_month_value) / prev_month_value) * 100
        
        return {
            "total_earned": float(total_earned.scalar() or 0),
            "pending_rewards": float(pending_rewards.scalar() or 0),
            "total_commissions": float(total_earned.scalar() or 0),
            "total_bonuses": 0,
            "current_month_earnings": float(current_month_value),
            "previous_month_earnings": float(prev_month_value),
            "growth_percentage": round(growth, 2)
        }
    
    async def get_transactions(
        self,
        db: AsyncSession,
        agent_id: UUID,
        skip: int = 0,
        limit: int = 10,
        status: Optional[str] = None,
        transaction_type: Optional[str] = None
    ) -> tuple[List[Transaction], int]:
        """Get transaction history"""
        query = select(Transaction).where(Transaction.agent_id == agent_id)
        
        if status:
            query = query.where(Transaction.status == status)
        if transaction_type:
            query = query.where(Transaction.type == transaction_type)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.execute(count_query)
        total_count = total.scalar()
        
        # Get paginated results
        query = query.order_by(desc(Transaction.created_at)).offset(skip).limit(limit)
        query = query.options(
            selectinload(Transaction.customer),
            selectinload(Transaction.agent)
        )
        result = await db.execute(query)
        transactions = result.scalars().all()
        
        return transactions, total_count
    
    # Wallet
    async def get_wallet_balance(self, db: AsyncSession, agent_id: UUID) -> Dict[str, Any]:
        """Get wallet balance"""
        earned_query = select(func.sum(Transaction.amount)).where(
            Transaction.agent_id == agent_id,
            Transaction.status == TransactionStatus.APPROVED,
            Transaction.type == TransactionType.CREDIT
        )
        total_earned = await db.execute(earned_query)
        
        withdrawn_query = select(func.sum(Transaction.amount)).where(
            Transaction.agent_id == agent_id,
            Transaction.status == TransactionStatus.APPROVED,
            Transaction.type == TransactionType.DEBIT
        )
        total_withdrawn = await db.execute(withdrawn_query)
        
        pending_query = select(func.sum(Transaction.amount)).where(
            Transaction.agent_id == agent_id,
            Transaction.status == TransactionStatus.PENDING,
            Transaction.type == TransactionType.CREDIT
        )
        pending_balance = await db.execute(pending_query)
        
        total_earned_value = total_earned.scalar() or 0
        total_withdrawn_value = total_withdrawn.scalar() or 0
        pending_balance_value = pending_balance.scalar() or 0
        
        balance = total_earned_value - total_withdrawn_value
        
        return {
            "balance": float(balance),
            "pending_balance": float(pending_balance_value),
            "total_earned": float(total_earned_value),
            "total_withdrawn": float(total_withdrawn_value),
            "currency": "NGN"
        }
    
    async def get_wallet_history(
        self,
        db: AsyncSession,
        agent_id: UUID,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Transaction], int]:
        """Get wallet history"""
        query = select(Transaction).where(
            Transaction.agent_id == agent_id,
            Transaction.status.in_([TransactionStatus.APPROVED, TransactionStatus.PENDING])
        )
        
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.execute(count_query)
        total_count = total.scalar()
        
        query = query.order_by(desc(Transaction.created_at)).offset(skip).limit(limit)
        result = await db.execute(query)
        transactions = result.scalars().all()
        
        return transactions, total_count
    
    async def get_payout_method(self, db: AsyncSession, agent_id: UUID) -> Optional[Dict]:
        """Get payout method"""
        query = select(Payment).where(
            Payment.agent_id == agent_id,
            Payment.status == PaymentStatus.PAID
        ).order_by(desc(Payment.created_at))
        
        result = await db.execute(query)
        payment = result.scalar_one_or_none()
        
        if not payment:
            return None
        
        return {
            "bank_name": payment.bank_name,
            "account_number": payment.bank_account[-4:] if payment.bank_account else "",
            "account_name": "John Doe",  # Would come from user
            "is_verified": True,
            "last_updated": payment.created_at
        }
    
    async def update_payout_method(
        self,
        db: AsyncSession,
        agent_id: UUID,
        payout_data: PayoutMethodUpdate
    ) -> Dict[str, Any]:
        """Update payout method"""
        return {
            "bank_name": payout_data.bank_name,
            "account_number": payout_data.account_number[-4:],
            "account_name": payout_data.account_name,
            "is_verified": False,
            "last_updated": datetime.now(timezone.utc)
        }
    
    # Profile
    async def get_profile(self, db: AsyncSession, agent_id: UUID) -> Optional[User]:
        """Get agent profile"""
        query = select(User).where(User.id == agent_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_profile(
        self,
        db: AsyncSession,
        agent_id: UUID,
        profile_data: AgentProfileUpdate
    ) -> Optional[User]:
        """Update agent profile"""
        user = await self.get_profile(db, agent_id)
        if not user:
            return None
        
        update_data = profile_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        
        await db.commit()
        await db.refresh(user)
        return user
    
    # Network
    async def get_network_stats(self, db: AsyncSession, agent_id: UUID) -> Dict[str, Any]:
        """Get referral network statistics"""
        downline_query = select(User).where(
            User.referral_partner_id == agent_id,
            User.role == "agent",
            User.status == "active"
        )
        result = await db.execute(downline_query)
        downline = result.scalars().all()
        
        revenue_query = select(func.sum(Transaction.amount)).where(
            Transaction.agent_id.in_([agent.id for agent in downline]),
            Transaction.status == TransactionStatus.APPROVED,
            Transaction.type == TransactionType.CREDIT
        )
        revenue_result = await db.execute(revenue_query)
        
        tier_breakdown = {}
        for agent in downline:
            tier = agent.agent_tier.value if agent.agent_tier else "unknown"
            tier_breakdown[tier] = tier_breakdown.get(tier, 0) + 1
        
        return {
            "total_downline": len(downline),
            "active_downline": len([a for a in downline if a.status == "active"]),
            "total_revenue_from_downline": float(revenue_result.scalar() or 0),
            "tier_breakdown": tier_breakdown
        }


agent_service = AgentService()