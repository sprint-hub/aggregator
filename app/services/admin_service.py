import uuid as uuid_lib
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime, timezone

from app.models.user import User, UserRole, UserStatus
from app.models.referral import ReferralCode, ReferralCodeStatus, Customer
from app.models.transaction import Transaction, TransactionStatus, TransactionType
from app.models.payment import Payment, PaymentStatus
from app.models.system_settings import SystemSetting
from app.schemas.user import UserCreate
from app.schemas.admin import (
    AdminAgentCreate,
    AdminAgentUpdate,
    AdminAgentStatusUpdate,
    AdminPaymentBatchCreate,
    AdminPaymentProcess,
    PlatformSettingsUpdate,
)
from app.core.security import get_password_hash

# Keys used for the "Platform Settings" screen, stored in system_settings
REWARD_PER_REFERRAL_KEY = "reward_per_referral"
MINIMUM_WITHDRAWAL_KEY = "minimum_withdrawal"
DEFAULT_REWARD_PER_REFERRAL = 50.0
DEFAULT_MINIMUM_WITHDRAWAL = 100.0


class AdminService:
    

    async def get_dashboard_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Get platform-wide overview statistics"""
        total_agents = (await db.execute(
            select(func.count()).where(User.role == UserRole.AGENT)
        )).scalar() or 0

        active_agents = (await db.execute(
            select(func.count()).where(
                User.role == UserRole.AGENT, User.status == UserStatus.ACTIVE
            )
        )).scalar() or 0

        pending_agents = (await db.execute(
            select(func.count()).where(
                User.role == UserRole.AGENT, User.status == UserStatus.PENDING
            )
        )).scalar() or 0

        total_customers = (await db.execute(select(func.count()).select_from(Customer))).scalar() or 0

        total_codes = (await db.execute(select(func.count()).select_from(ReferralCode))).scalar() or 0

        active_codes = (await db.execute(
            select(func.count()).where(ReferralCode.status == ReferralCodeStatus.ACTIVE)
        )).scalar() or 0

        pending_rewards_q = select(
            func.count(), func.coalesce(func.sum(Transaction.amount), 0)
        ).where(
            Transaction.status == TransactionStatus.PENDING,
            Transaction.type == TransactionType.CREDIT,
        )
        pending_rewards_count, pending_rewards_amount = (await db.execute(pending_rewards_q)).one()

        pending_payments_q = select(
            func.count(), func.coalesce(func.sum(Payment.amount), 0)
        ).where(Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.PROCESSING]))
        pending_payments_count, pending_payments_amount = (await db.execute(pending_payments_q)).one()

        total_revenue = (await db.execute(
            select(func.coalesce(func.sum(ReferralCode.revenue_generated), 0))
        )).scalar() or 0

        total_paid_out = (await db.execute(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.status == PaymentStatus.PAID
            )
        )).scalar() or 0

        return {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "pending_agents": pending_agents,
            "total_customers": total_customers,
            "total_referral_codes": total_codes,
            "active_referral_codes": active_codes,
            "pending_rewards_count": pending_rewards_count or 0,
            "pending_rewards_amount": float(pending_rewards_amount or 0),
            "pending_payments_count": pending_payments_count or 0,
            "pending_payments_amount": float(pending_payments_amount or 0),
            "total_revenue": float(total_revenue),
            "total_paid_out": float(total_paid_out),
        }


    async def list_agents(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 10,
        status: Optional[str] = None,
        agent_tier: Optional[str] = None,
        region: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """List agents with filters, search, and per-agent customer/earnings summary"""
        query = select(User).where(User.role == UserRole.AGENT)

        if status:
            query = query.where(User.status == status)
        if agent_tier:
            query = query.where(User.agent_tier == agent_tier)
        if region:
            query = query.where(User.region == region)
        if search:
            like = f"%{search}%"
            query = query.where(
                or_(
                    User.first_name.ilike(like),
                    User.last_name.ilike(like),
                    User.email.ilike(like),
                    User.agent_code.ilike(like),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        query = query.order_by(desc(User.created_at)).offset(skip).limit(limit)
        agents = (await db.execute(query)).scalars().all()

        results = []
        for agent in agents:
            customers_count = (await db.execute(
                select(func.count()).where(Customer.agent_id == agent.id)
            )).scalar() or 0

            total_earned = (await db.execute(
                select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                    Transaction.agent_id == agent.id,
                    Transaction.status == TransactionStatus.APPROVED,
                    Transaction.type == TransactionType.CREDIT,
                )
            )).scalar() or 0

            results.append({
                "id": agent.id,
                "email": agent.email,
                "first_name": agent.first_name,
                "last_name": agent.last_name,
                "agent_code": agent.agent_code,
                "agent_tier": agent.agent_tier.value if agent.agent_tier else None,
                "region": agent.region,
                "status": agent.status.value,
                "efficiency_score": agent.efficiency_score,
                "customers_count": customers_count,
                "total_earned": float(total_earned),
                "created_at": agent.created_at,
            })

        return results, total

    async def get_agent(self, db: AsyncSession, agent_id: UUID) -> Optional[User]:
        """Get a single agent by ID"""
        query = select(User).where(User.id == agent_id, User.role == UserRole.AGENT)
        return (await db.execute(query)).scalar_one_or_none()

    async def create_agent(self, db: AsyncSession, data: AdminAgentCreate) -> User:
        """Admin-initiated agent creation"""
        existing = await db.execute(select(User).where(User.email == data.email.lower()))
        if existing.scalar_one_or_none():
            raise ValueError("A user with this email already exists")

        user_data = UserCreate(
            email=data.email,
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            role=UserRole.AGENT,
            agent_tier=data.agent_tier,
            region=data.region,
        )
        user = User(
            email=user_data.email.lower(),
            password_hash=get_password_hash(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            role=UserRole.AGENT,
            status=UserStatus.ACTIVE,
            agent_tier=user_data.agent_tier,
            region=user_data.region,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def update_agent(
        self, db: AsyncSession, agent_id: UUID, data: AdminAgentUpdate
    ) -> Optional[User]:
        """Update an agent's profile fields"""
        agent = await self.get_agent(db, agent_id)
        if not agent:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(agent, key, value)

        await db.commit()
        await db.refresh(agent)
        return agent

    async def update_agent_status(
        self, db: AsyncSession, agent_id: UUID, data: AdminAgentStatusUpdate
    ) -> Optional[User]:
        """Suspend or reactivate an agent"""
        agent = await self.get_agent(db, agent_id)
        if not agent:
            return None

        agent.status = data.status
        await db.commit()
        await db.refresh(agent)
        return agent
    

    async def list_referral_codes(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 10,
        status: Optional[str] = None,
        agent_id: Optional[UUID] = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """List referral codes across all agents"""
        query = select(ReferralCode).options(selectinload(ReferralCode.agent))

        if status:
            try:
                status_enum = ReferralCodeStatus(status.lower())
            except ValueError:
                valid = ", ".join(s.value for s in ReferralCodeStatus)
                raise ValueError(f"Invalid status '{status}'. Must be one of: {valid}")
            query = query.where(ReferralCode.status == status_enum)
        if agent_id:
            query = query.where(ReferralCode.agent_id == agent_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        query = query.order_by(desc(ReferralCode.created_at)).offset(skip).limit(limit)
        codes = (await db.execute(query)).scalars().all()

        results = [{
            "id": c.id,
            "code": c.code,
            "agent_id": c.agent_id,
            "agent_name": f"{c.agent.first_name} {c.agent.last_name}" if c.agent else "",
            "bank": c.bank,
            "status": c.status.value,
            "customers_referred": c.customers_referred,
            "revenue_generated": c.revenue_generated,
            "expires_at": c.expires_at,
            "created_at": c.created_at,
        } for c in codes]

        return results, total

    async def update_referral_code_status(
        self, db: AsyncSession, code_id: UUID, status: str
    ) -> Optional[ReferralCode]:
        """Admin override of a referral code's status"""
        try:
            status_enum = ReferralCodeStatus(status.lower())
        except ValueError:
            valid = ", ".join(s.value for s in ReferralCodeStatus)
            raise ValueError(f"Invalid status '{status}'. Must be one of: {valid}")

        query = select(ReferralCode).where(ReferralCode.id == code_id)
        code = (await db.execute(query)).scalar_one_or_none()
        if not code:
            return None

        code.status = status_enum
        await db.commit()
        await db.refresh(code)
        return code

    
    async def list_rewards(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 10,
        status: Optional[str] = None,
        agent_id: Optional[UUID] = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """List reward transactions (credit-type transactions) for review"""
        query = select(Transaction).where(Transaction.type == TransactionType.CREDIT).options(
            selectinload(Transaction.agent),
            selectinload(Transaction.customer),
        )

        if status:
            try:
                status_enum = TransactionStatus(status.lower())
            except ValueError:
                valid = ", ".join(s.value for s in TransactionStatus)
                raise ValueError(f"Invalid status '{status}'. Must be one of: {valid}")
            query = query.where(Transaction.status == status_enum)
        if agent_id:
            query = query.where(Transaction.agent_id == agent_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        query = query.order_by(desc(Transaction.created_at)).offset(skip).limit(limit)
        transactions = (await db.execute(query)).scalars().all()

        # Referral codes are looked up separately since Transaction only stores the FK
        code_ids = [t.referral_code_id for t in transactions if t.referral_code_id]
        codes_by_id = {}
        if code_ids:
            codes_result = await db.execute(
                select(ReferralCode).where(ReferralCode.id.in_(code_ids))
            )
            codes_by_id = {c.id: c.code for c in codes_result.scalars().all()}

        results = [{
            "id": t.id,
            "reward_id": t.transaction_id,
            "agent_id": t.agent_id,
            "agent_name": f"{t.agent.first_name} {t.agent.last_name}" if t.agent else "",
            "referral_code": codes_by_id.get(t.referral_code_id),
            "customer_id": t.customer_id,
            "amount": t.amount,
            "status": t.status.value,
            "created_at": t.created_at,
        } for t in transactions]

        return results, total

    async def get_reward(self, db: AsyncSession, reward_id: UUID) -> Optional[Transaction]:
        """Get a single reward transaction by ID"""
        query = select(Transaction).where(
            Transaction.id == reward_id, Transaction.type == TransactionType.CREDIT
        )
        return (await db.execute(query)).scalar_one_or_none()

    async def approve_reward(self, db: AsyncSession, reward_id: UUID) -> Optional[Transaction]:
        """Approve a pending reward"""
        reward = await self.get_reward(db, reward_id)
        if not reward:
            return None
        if reward.status != TransactionStatus.PENDING:
            raise ValueError("Only pending rewards can be approved")

        reward.status = TransactionStatus.APPROVED
        await db.commit()
        await db.refresh(reward)
        return reward

    async def reject_reward(
        self, db: AsyncSession, reward_id: UUID, reason: Optional[str] = None
    ) -> Optional[Transaction]:
        """Reject a pending reward"""
        reward = await self.get_reward(db, reward_id)
        if not reward:
            return None
        if reward.status != TransactionStatus.PENDING:
            raise ValueError("Only pending rewards can be rejected")

        reward.status = TransactionStatus.REJECTED
        if reason:
            reward.description = (reward.description or "") + f" | Rejected: {reason}"
        await db.commit()
        await db.refresh(reward)
        return reward

    
    async def list_payments(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 10,
        status: Optional[str] = None,
        agent_id: Optional[UUID] = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """List payments across all agents"""
        query = select(Payment).options(selectinload(Payment.agent))

        if status:
            try:
                status_enum = PaymentStatus(status.lower())
            except ValueError:
                valid = ", ".join(s.value for s in PaymentStatus)
                raise ValueError(f"Invalid status '{status}'. Must be one of: {valid}")
            query = query.where(Payment.status == status_enum)
        if agent_id:
            query = query.where(Payment.agent_id == agent_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        query = query.order_by(desc(Payment.payment_date)).offset(skip).limit(limit)
        payments = (await db.execute(query)).scalars().all()

        results = [{
            "id": p.id,
            "payment_id": p.payment_id,
            "agent_id": p.agent_id,
            "agent_name": f"{p.agent.first_name} {p.agent.last_name}" if p.agent else "",
            "amount": p.amount,
            "payment_date": p.payment_date,
            "status": p.status.value,
            "bank_name": p.bank_name,
            "transaction_reference": p.transaction_reference,
        } for p in payments]

        return results, total

    async def create_payment_batch(
        self, db: AsyncSession, data: AdminPaymentBatchCreate
    ) -> Dict[str, Any]:
    
        payment_date = data.payment_date or datetime.now(timezone.utc)
        created_payments: List[Payment] = []

        for agent_id in data.agent_ids:
            agent_query = select(User).where(User.id == agent_id)
            agent = (await db.execute(agent_query)).scalar_one_or_none()
            if not agent:
                continue

            owed_query = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.agent_id == agent_id,
                Transaction.status == TransactionStatus.APPROVED,
                Transaction.type == TransactionType.CREDIT,
                Transaction.payment_id.is_(None),
            )
            owed = (await db.execute(owed_query)).scalar() or 0

            if owed <= 0:
                continue

            payment = Payment(
                payment_id=f"PAY-{uuid_lib.uuid4().hex[:6].upper()}",
                agent_id=agent_id,
                amount=float(owed),
                payment_date=payment_date,
                status=PaymentStatus.PENDING,
                bank_name=agent.default_bank_name,
                bank_account=agent.bank_account_last4,
            )
            db.add(payment)
            await db.flush()

            # Tag the underlying reward transactions as claimed by this payment
            update_query = select(Transaction).where(
                Transaction.agent_id == agent_id,
                Transaction.status == TransactionStatus.APPROVED,
                Transaction.type == TransactionType.CREDIT,
                Transaction.payment_id.is_(None),
            )
            txns = (await db.execute(update_query)).scalars().all()
            for txn in txns:
                txn.payment_id = payment.payment_id

            created_payments.append(payment)

        await db.commit()
        for p in created_payments:
            await db.refresh(p)

        batch_id = f"BATCH-{uuid_lib.uuid4().hex[:8].upper()}"
        return {
            "batch_id": batch_id,
            "payments_created": len(created_payments),
            "total_amount": sum(p.amount for p in created_payments),
            "payments": created_payments,
        }

    async def process_payment(
        self, db: AsyncSession, payment_id: UUID, data: AdminPaymentProcess
    ) -> Optional[Payment]:
        """Advance a payment's status ('Process Payment' action)"""
        try:
            status_enum = PaymentStatus(data.status.lower())
        except ValueError:
            valid = ", ".join(s.value for s in PaymentStatus)
            raise ValueError(f"Invalid status '{data.status}'. Must be one of: {valid}")

        query = select(Payment).where(Payment.id == payment_id)
        payment = (await db.execute(query)).scalar_one_or_none()
        if not payment:
            return None

        payment.status = status_enum
        if data.transaction_reference:
            payment.transaction_reference = data.transaction_reference

        await db.commit()
        await db.refresh(payment)
        return payment

   
    async def get_agent_performance_report(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 10,
        region: Optional[str] = None,
        agent_tier: Optional[str] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """Agent performance breakdown for the Reports & Analytics screen"""
        query = select(User).where(User.role == UserRole.AGENT)
        if region:
            query = query.where(User.region == region)
        if agent_tier:
            query = query.where(User.agent_tier == agent_tier)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        query = query.order_by(desc(User.efficiency_score)).offset(skip).limit(limit)
        agents = (await db.execute(query)).scalars().all()

        results = []
        for agent in agents:
            referrals_query = select(func.count()).where(Customer.agent_id == agent.id)
            if period_start:
                referrals_query = referrals_query.where(Customer.created_at >= period_start)
            if period_end:
                referrals_query = referrals_query.where(Customer.created_at <= period_end)
            referrals = (await db.execute(referrals_query)).scalar() or 0

            revenue_query = select(func.coalesce(func.sum(ReferralCode.revenue_generated), 0)).where(
                ReferralCode.agent_id == agent.id
            )
            revenue = (await db.execute(revenue_query)).scalar() or 0

            commission_query = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.agent_id == agent.id,
                Transaction.status == TransactionStatus.APPROVED,
                Transaction.type == TransactionType.CREDIT,
            )
            commission = (await db.execute(commission_query)).scalar() or 0

            results.append({
                "agent_id": agent.id,
                "agent_name": f"{agent.first_name} {agent.last_name}",
                "agent_code": agent.agent_code,
                "region": agent.region,
                "referrals": referrals,
                "revenue": float(revenue),
                "commission": float(commission),
                "status": agent.status.value,
            })

        return results, total

    
    async def _get_or_default(self, db: AsyncSession, key: str, default: float) -> float:
        query = select(SystemSetting).where(SystemSetting.key == key)
        setting = (await db.execute(query)).scalar_one_or_none()
        if setting is None:
            return default
        return float(setting.value)

    async def get_platform_settings(self, db: AsyncSession) -> Dict[str, Any]:
        """Get the 'Referral Program Settings' values shown on the Settings screen"""
        reward_per_referral = await self._get_or_default(
            db, REWARD_PER_REFERRAL_KEY, DEFAULT_REWARD_PER_REFERRAL
        )
        minimum_withdrawal = await self._get_or_default(
            db, MINIMUM_WITHDRAWAL_KEY, DEFAULT_MINIMUM_WITHDRAWAL
        )
        return {
            "reward_per_referral": reward_per_referral,
            "minimum_withdrawal": minimum_withdrawal,
        }

    async def update_platform_settings(
        self, db: AsyncSession, data: PlatformSettingsUpdate
    ) -> Dict[str, Any]:
        """Upsert the platform settings changed via 'Save Changes'"""
        updates = {}
        if data.reward_per_referral is not None:
            updates[REWARD_PER_REFERRAL_KEY] = data.reward_per_referral
        if data.minimum_withdrawal is not None:
            updates[MINIMUM_WITHDRAWAL_KEY] = data.minimum_withdrawal

        for key, value in updates.items():
            query = select(SystemSetting).where(SystemSetting.key == key)
            setting = (await db.execute(query)).scalar_one_or_none()
            if setting:
                setting.value = value
            else:
                db.add(SystemSetting(
                    key=key,
                    value=value,
                    category="referral_program",
                    is_public=False,
                ))

        await db.commit()
        return await self.get_platform_settings(db)

admin_service = AdminService()
