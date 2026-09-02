from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.permissions import AdminRequired
from app.models.user import User
from app.services.admin_service import admin_service
from app.schemas.admin import AdminReferralCodeListResponse, AdminReferralCodeStatusUpdate

router = APIRouter()


@router.get("/", response_model=AdminReferralCodeListResponse)
async def list_referral_codes(
    current_user: User = Depends(AdminRequired),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    agent_id: Optional[UUID] = None,
):
    """List referral codes across all agents"""
    try:
        codes, total = await admin_service.list_referral_codes(db, skip, limit, status, agent_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "codes": codes,
        "total": total,
        "page": skip // limit + 1,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
    }


@router.put("/{code_id}/status")
async def update_referral_code_status(
    code_id: UUID,
    data: AdminReferralCodeStatusUpdate,
    current_user: User = Depends(AdminRequired),
    db: AsyncSession = Depends(get_db)
):
    """Admin override of a referral code's status"""
    try:
        code = await admin_service.update_referral_code_status(db, code_id, data.status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not code:
        raise HTTPException(status_code=404, detail="Referral code not found")
    return {"message": "Referral code status updated successfully"}
