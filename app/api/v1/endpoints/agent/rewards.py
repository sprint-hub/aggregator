from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.permissions import AgentRequired
from app.models.user import User
from app.services.agent_service import agent_service
from app.schemas.agent import (
    RewardsSummaryResponse,
    TransactionListResponse
)

router = APIRouter()


@router.get("/summary", response_model=RewardsSummaryResponse)
async def get_rewards_summary(
    current_user: User = Depends(AgentRequired),
    db: AsyncSession = Depends(get_db)
):
    """Get rewards overview"""
    summary = await agent_service.get_rewards_summary(db, current_user.id)
    return summary


@router.get("/transactions", response_model=TransactionListResponse)
async def get_transactions(
    current_user: User = Depends(AgentRequired),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    transaction_type: Optional[str] = None
):
    """Get transaction history"""
    transactions, total = await agent_service.get_transactions(
        db, current_user.id, skip, limit, status, transaction_type
    )
    
    return {
        "transactions": transactions,
        "total": total,
        "page": skip // limit + 1,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    }