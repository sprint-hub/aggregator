from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import AgentRequired
from app.models.user import User
from app.services.agent_service import agent_service
from app.schemas.agent import NetworkStatsResponse

router = APIRouter()


@router.get("/stats", response_model=NetworkStatsResponse)
async def get_network_stats(
    current_user: User = Depends(AgentRequired),
    db: AsyncSession = Depends(get_db)
):
    """Get referral network statistics"""
    stats = await agent_service.get_network_stats(db, current_user.id)
    return stats