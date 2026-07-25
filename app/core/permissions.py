from typing import List, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import oauth2_scheme, decode_token
from app.services.user_service import user_service


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Get current authenticated user from JWT token"""
    payload = decode_token(token)
    user_id = payload.get("user_id")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    user = await user_service.get_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Check if user is active
    if hasattr(user, 'status') and user.status == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account suspended",
        )

    return user


def require_roles(allowed_roles: List[str]):
    """Dependency factory for role-based access control"""
    async def dependency(current_user = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}",
            )
        return current_user
    return dependency


# Convenience dependencies
AgentRequired = require_roles(["agent"])
AdminRequired = require_roles(["admin", "super_admin"])
SuperAdminRequired = require_roles(["super_admin"])