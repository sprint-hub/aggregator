from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.permissions import AdminRequired
from app.models.user import User
from app.services.admin_service import admin_service
from app.schemas.admin import (
    AdminAgentListResponse,
    AdminAgentDetailResponse,
    AdminAgentCreate,
    AdminAgentUpdate,
    AdminAgentStatusUpdate,
)

router = APIRouter()


@router.get("/", response_model=AdminAgentListResponse)
async def list_agents(
    current_user: User = Depends(AdminRequired),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    agent_tier: Optional[str] = None,
    region: Optional[str] = None,
    search: Optional[str] = Query(None, description="Search by name, email, or agent code"),
):
    """List agents with filters and search"""
    agents, total = await admin_service.list_agents(
        db, skip, limit, status, agent_tier, region, search
    )
    return {
        "agents": agents,
        "total": total,
        "page": skip // limit + 1,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
    }


@router.post("/", response_model=AdminAgentDetailResponse)
async def create_agent(
    data: AdminAgentCreate,
    current_user: User = Depends(AdminRequired),
    db: AsyncSession = Depends(get_db)
):
    """Create a new agent on their behalf"""
    try:
        agent = await admin_service.create_agent(db, data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return agent


@router.get("/{agent_id}", response_model=AdminAgentDetailResponse)
async def get_agent(
    agent_id: UUID,
    current_user: User = Depends(AdminRequired),
    db: AsyncSession = Depends(get_db)
):
    """Get a single agent's full detail"""
    agent = await admin_service.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}", response_model=AdminAgentDetailResponse)
async def update_agent(
    agent_id: UUID,
    data: AdminAgentUpdate,
    current_user: User = Depends(AdminRequired),
    db: AsyncSession = Depends(get_db)
):
    """Update an agent's profile"""
    agent = await admin_service.update_agent(db, agent_id, data)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}/status", response_model=AdminAgentDetailResponse)
async def update_agent_status(
    agent_id: UUID,
    data: AdminAgentStatusUpdate,
    current_user: User = Depends(AdminRequired),
    db: AsyncSession = Depends(get_db)
):
    """Suspend or reactivate an agent"""
    agent = await admin_service.update_agent_status(db, agent_id, data)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent
