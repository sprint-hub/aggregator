from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from uuid import UUID
import uuid
from datetime import datetime

from app.models.user import User, UserRole, UserStatus, AgentTier
from app.core.security import get_password_hash, verify_password
from app.schemas.user import UserCreate, UserUpdate, UserInDB


class UserService:
    async def get_by_id(self, db: AsyncSession, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        query = select(User).where(User.email == email.lower())
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_agent_code(self, db: AsyncSession, agent_code: str) -> Optional[User]:
        """Get agent by agent code"""
        query = select(User).where(User.agent_code == agent_code)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_agents(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 10,
        status: Optional[str] = None,
        tier: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple[List[User], int]:
        """Get all agents with filters"""
        query = select(User).where(User.role == UserRole.AGENT)
        
        if status:
            query = query.where(User.status == status)
        if tier:
            query = query.where(User.agent_tier == tier)
        if search:
            query = query.where(
                (User.email.ilike(f"%{search}%")) |
                (User.first_name.ilike(f"%{search}%")) |
                (User.last_name.ilike(f"%{search}%")) |
                (User.agent_code.ilike(f"%{search}%"))
            )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.execute(count_query)
        total_count = total.scalar()
        
        # Get paginated results
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        users = result.scalars().all()
        
        return users, total_count

    async def create(self, db: AsyncSession, user_data: UserCreate) -> User:
        """Create new user"""
        password_hash = get_password_hash(user_data.password)
        
        # Generate agent code if not provided
        agent_code = user_data.agent_code
        if user_data.role == UserRole.AGENT and not agent_code:
            agent_code = f"AGENT-{uuid.uuid4().hex[:8].upper()}"
        
        user = User(
            email=user_data.email.lower(),
            password_hash=password_hash,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            role=user_data.role or UserRole.AGENT,
            status=user_data.status or UserStatus.PENDING,
            agent_code=agent_code,
            agent_tier=user_data.agent_tier,
            region=user_data.region,
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def update(self, db: AsyncSession, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
        """Update user"""
        user = await self.get_by_id(db, user_id)
        if not user:
            return None

        update_data = user_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == "password":
                value = get_password_hash(value)
            setattr(user, key, value)

        await db.commit()
        await db.refresh(user)
        return user

    async def update_status(self, db: AsyncSession, user_id: UUID, status: UserStatus) -> Optional[User]:
        """Update user status"""
        user = await self.get_by_id(db, user_id)
        if not user:
            return None
        
        user.status = status
        await db.commit()
        await db.refresh(user)
        return user

    async def authenticate(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate user"""
        user = await self.get_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    async def update_last_login(self, db: AsyncSession, user_id: UUID, ip: str = None):
        """Update last login timestamp"""
        user = await self.get_by_id(db, user_id)
        if user:
            user.last_login_at = datetime.utcnow()
            if ip:
                user.last_login_ip = ip
            await db.commit()

    async def get_agent_stats(self, db: AsyncSession, agent_id: UUID) -> Dict[str, Any]:
        """Get agent statistics"""
        from app.models.referral import ReferralCode, Customer
        from app.models.transaction import Transaction
        
        # Get total codes
        codes_query = select(func.count()).where(ReferralCode.agent_id == agent_id)
        total_codes = await db.execute(codes_query)
        
        # Get total customers
        customers_query = select(func.count()).where(Customer.agent_id == agent_id)
        total_customers = await db.execute(customers_query)
        
        # Get completed signups (active customers)
        active_query = select(func.count()).where(
            Customer.agent_id == agent_id,
            Customer.status.in_(['active', 'premium'])
        )
        completed_signups = await db.execute(active_query)
        
        # Get pending customers
        pending_query = select(func.count()).where(
            Customer.agent_id == agent_id,
            Customer.status == 'pending'
        )
        pending_verification = await db.execute(pending_query)
        
        # Get in-progress (KYC in progress)
        in_progress_query = select(func.count()).where(
            Customer.agent_id == agent_id,
            Customer.status == 'kyc_in_progress'
        )
        in_progress = await db.execute(in_progress_query)
        
        return {
            "total_codes": total_codes.scalar() or 0,
            "total_customers": total_customers.scalar() or 0,
            "completed_signups": completed_signups.scalar() or 0,
            "pending_verification": pending_verification.scalar() or 0,
            "in_progress": in_progress.scalar() or 0,
        }


user_service = UserService()