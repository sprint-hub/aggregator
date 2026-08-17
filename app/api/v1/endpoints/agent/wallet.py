from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import AgentRequired
from app.models.user import User
from app.services.agent_service import agent_service
from app.schemas.agent import (
    WalletBalanceResponse,
    PayoutMethodResponse,
    PayoutMethodUpdate
)

router = APIRouter()


@router.get("/balance", response_model=WalletBalanceResponse)
async def get_wallet_balance(
    current_user: User = Depends(AgentRequired),
    db: AsyncSession = Depends(get_db)
):
    """Get wallet balance"""
    balance = await agent_service.get_wallet_balance(db, current_user.id)
    return balance


@router.get("/history")
async def get_wallet_history(
    current_user: User = Depends(AgentRequired),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """Get wallet history"""
    transactions, total = await agent_service.get_wallet_history(
        db, current_user.id, skip, limit
    )
    
    return {
        "transactions": transactions,
        "total": total,
        "page": skip // limit + 1,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    }


@router.get("/payout-method", response_model=PayoutMethodResponse)
async def get_payout_method(
    current_user: User = Depends(AgentRequired),
    db: AsyncSession = Depends(get_db)
):
    """Get payout method"""
    method = await agent_service.get_payout_method(db, current_user.id)
    if not method:
        raise HTTPException(status_code=404, detail="No payout method found")
    return method


@router.put("/payout-method", response_model=PayoutMethodResponse)
async def update_payout_method(
    payout_data: PayoutMethodUpdate,
    current_user: User = Depends(AgentRequired),
    db: AsyncSession = Depends(get_db)
):
    """Update payout method"""
    method = await agent_service.update_payout_method(db, current_user.id, payout_data)
    return method