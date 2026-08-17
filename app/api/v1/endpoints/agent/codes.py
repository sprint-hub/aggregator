from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.permissions import AgentRequired
from app.models.user import User
from app.services.agent_service import agent_service
from app.schemas.agent import (
    ReferralCodeCreate,
    ReferralCodeUpdate,
    ReferralCodeResponse
)

router = APIRouter()


@router.get("/", response_model=dict)
async def get_codes(
    current_user: User = Depends(AgentRequired),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = None
):
    """Get agent's referral codes"""
    codes, total = await agent_service.get_codes(
        db, current_user.id, skip, limit, status
    )
    
    return {
        "codes": codes,
        "total": total,
        "page": skip // limit + 1,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    }


@router.post("/", response_model=ReferralCodeResponse)
async def create_code(
    code_data: ReferralCodeCreate,
    current_user: User = Depends(AgentRequired),
    db: AsyncSession = Depends(get_db)
):
    """Create a new referral code"""
    code = await agent_service.create_code(db, current_user.id, code_data)
    return code


@router.get("/{code_id}", response_model=ReferralCodeResponse)
async def get_code(
    code_id: UUID,
    current_user: User = Depends(AgentRequired),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific referral code"""
    code = await agent_service.get_code(db, code_id, current_user.id)
    if not code:
        raise HTTPException(status_code=404, detail="Referral code not found")
    return code


@router.put("/{code_id}", response_model=ReferralCodeResponse)
async def update_code(
    code_id: UUID,
    code_data: ReferralCodeUpdate,
    current_user: User = Depends(AgentRequired),
    db: AsyncSession = Depends(get_db)
):
    """Update a referral code"""
    code = await agent_service.update_code(db, code_id, current_user.id, code_data)
    if not code:
        raise HTTPException(status_code=404, detail="Referral code not found")
    return code


@router.delete("/{code_id}")
async def delete_code(
    code_id: UUID,
    current_user: User = Depends(AgentRequired),
    db: AsyncSession = Depends(get_db)
):
    """Delete (deactivate) a referral code"""
    success = await agent_service.delete_code(db, code_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Referral code not found")
    return {"message": "Referral code deactivated successfully"}