from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.permissions import AdminRequired
from app.models.user import User
from app.services.admin_service import admin_service
from app.schemas.admin import AdminRewardListResponse, AdminRewardDecision

router = APIRouter()


@router.get("/", response_model=AdminRewardListResponse)
async def list_rewards(
    current_user: User = Depends(AdminRequired),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    agent_id: Optional[UUID] = None,
):
    """List reward transactions awaiting review, with filters"""
    try:
        rewards, total = await admin_service.list_rewards(db, skip, limit, status, agent_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "rewards": rewards,
        "total": total,
        "page": skip // limit + 1,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
    }


@router.put("/{reward_id}/approve")
async def approve_reward(
    reward_id: UUID,
    current_user: User = Depends(AdminRequired),
    db: AsyncSession = Depends(get_db)
):
    """Approve a pending reward"""
    try:
        reward = await admin_service.approve_reward(db, reward_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    return {"message": "Reward approved successfully"}


@router.put("/{reward_id}/reject")
async def reject_reward(
    reward_id: UUID,
    data: AdminRewardDecision,
    current_user: User = Depends(AdminRequired),
    db: AsyncSession = Depends(get_db)
):
    """Reject a pending reward"""
    try:
        reward = await admin_service.reject_reward(db, reward_id, data.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    return {"message": "Reward rejected successfully"}
