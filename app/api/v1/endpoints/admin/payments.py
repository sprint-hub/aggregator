from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.permissions import AdminRequired
from app.models.user import User
from app.services.admin_service import admin_service
from app.schemas.admin import (
    AdminPaymentListResponse,
    AdminPaymentBatchCreate,
    AdminPaymentBatchResponse,
    AdminPaymentProcess,
)

router = APIRouter()


@router.get("/", response_model=AdminPaymentListResponse)
async def list_payments(
    current_user: User = Depends(AdminRequired),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    agent_id: Optional[UUID] = None,
):
    """List payments across all agents"""
    payments, total = await admin_service.list_payments(db, skip, limit, status, agent_id)
    return {
        "payments": payments,
        "total": total,
        "page": skip // limit + 1,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
    }


@router.post("/batch", response_model=AdminPaymentBatchResponse)
async def create_payment_batch(
    data: AdminPaymentBatchCreate,
    current_user: User = Depends(AdminRequired),
    db: AsyncSession = Depends(get_db)
):
    """Create a payment batch for agents with an outstanding approved balance"""
    batch = await admin_service.create_payment_batch(db, data)
    return batch


@router.put("/{payment_id}/process")
async def process_payment(
    payment_id: UUID,
    data: AdminPaymentProcess,
    current_user: User = Depends(AdminRequired),
    db: AsyncSession = Depends(get_db)
):
    """Advance a payment's status (processing / paid / failed)"""
    payment = await admin_service.process_payment(db, payment_id, data)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"message": "Payment updated successfully"}
