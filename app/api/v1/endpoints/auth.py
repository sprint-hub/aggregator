from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import create_access_token, decode_token
from app.services.auth_service import auth_service
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    TokenRefreshRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
)
from app.core.permissions import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Login endpoint for agents and admins"""
    # Get client IP for logging
    client_ip = request.client.host if request.client else None

    user, access_token, refresh_token = await auth_service.login(
        db, login_data.email, login_data.password, client_ip
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Check if user is active
    if user.status == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been suspended",
        )

    # Build user response
    user_data = {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role.value,
        "status": user.status.value,
        "agent_code": user.agent_code,
        "agent_tier": user.agent_tier.value if user.agent_tier else None,
        "avatar": user.avatar,
        "region": user.region,
        "efficiency_score": user.efficiency_score,
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
    }

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 3600,  # 1 hour
        "user": user_data,
    }


@router.post("/refresh")
async def refresh_token(
    refresh_data: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token"""
    access_token, refresh_token = await auth_service.refresh_token(
        db, refresh_data.refresh_token
    )

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 3600,
    }


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout endpoint - client should discard token"""
    # Token invalidation can be handled with a blacklist in Redis
    return {"message": "Successfully logged out"}


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Request password reset"""
    # For now, just return success (email sending will be implemented later)
    # In production, you'd check if user exists and send email
    return {"message": "Password reset instructions sent to email"}


@router.post("/reset-password")
async def reset_password(
    reset_data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Reset password with token"""
    if reset_data.new_password != reset_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )

    # Decode token and get user
    try:
        payload = decode_token(reset_data.token)
        user_id = payload.get("user_id")
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token",
        )

    # Update password
    from app.services.user_service import user_service
    from app.core.security import get_password_hash

    user = await user_service.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.password_hash = get_password_hash(reset_data.new_password)
    await db.commit()

    return {"message": "Password reset successful"}


@router.put("/change-password")
async def change_password(
    change_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change password while logged in"""
    if change_data.new_password != change_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )

    success = await auth_service.change_password(
        db,
        current_user.id,
        change_data.current_password,
        change_data.new_password,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    return {"message": "Password changed successfully"}


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role.value,
        "status": current_user.status.value,
        "agent_code": current_user.agent_code,
        "agent_tier": current_user.agent_tier.value if current_user.agent_tier else None,
        "avatar": current_user.avatar,
        "region": current_user.region,
        "efficiency_score": current_user.efficiency_score,
        "created_at": current_user.created_at,
        "last_login_at": current_user.last_login_at,
    }