from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import AgentRequired
from app.models.user import User
from app.services.agent_service import agent_service
from app.schemas.agent import AgentProfileResponse, AgentProfileUpdate

router = APIRouter()


@router.get("/", response_model=AgentProfileResponse)
async def get_profile(
    current_user: User = Depends(AgentRequired),
    db: AsyncSession = Depends(get_db)
):
    """Get agent profile"""
    profile = await agent_service.get_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/", response_model=AgentProfileResponse)
async def update_profile(
    profile_data: AgentProfileUpdate,
    current_user: User = Depends(AgentRequired),
    db: AsyncSession = Depends(get_db)
):
    """Update agent profile"""
    profile = await agent_service.update_profile(db, current_user.id, profile_data)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile