from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.models.user import User, UserRole, UserStatus, AgentTier
from app.core.security import get_password_hash, verify_password
from app.schemas.user import UserCreate, UserUpdate


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

    async def create(self, db: AsyncSession, user_data: UserCreate) -> User:
        """Create new user"""
        password_hash = get_password_hash(user_data.password)

        user = User(
            email=user_data.email.lower(),
            password_hash=password_hash,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            role=user_data.role or UserRole.AGENT,
            status=UserStatus.PENDING,
            agent_code=user_data.agent_code,
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
            from datetime import datetime
            user.last_login_at = datetime.utcnow()
            if ip:
                user.last_login_ip = ip
            await db.commit()


user_service = UserService()