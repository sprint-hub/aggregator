from typing import Tuple, Dict, Any
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.services.user_service import user_service
from app.schemas.auth import LoginResponse, TokenRefreshRequest


class AuthService:
    async def login(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        ip: str = None
    ) -> Tuple[Dict[str, Any], str, str]:
        """Authenticate user and generate tokens"""
        user = await user_service.authenticate(db, email, password)
        if not user:
            return None, None, None

        await user_service.update_last_login(db, user.id, ip)

        token_data = {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role.value
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return user, access_token, refresh_token

    async def refresh_token(
        self,
        db: AsyncSession,
        refresh_token: str
    ) -> Tuple[str, str]:
        
        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            return None, None

        user_id = payload.get("user_id")
        user = await user_service.get_by_id(db, user_id)

        if not user:
            return None, None

        token_data = {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role.value
        }

        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)

        return new_access_token, new_refresh_token

    async def change_password(
        self,
        db: AsyncSession,
        user_id: str,
        current_password: str,
        new_password: str
    ) -> bool:
        """Change user password"""
        user = await user_service.get_by_id(db, user_id)
        if not user:
            return False

        from app.core.security import verify_password, get_password_hash
        if not verify_password(current_password, user.password_hash):
            return False

        user.password_hash = get_password_hash(new_password)
        await db.commit()
        return True


auth_service = AuthService()