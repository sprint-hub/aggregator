from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.permissions import AdminRequired
from app.models.user import User
from app.services.admin_service import admin_service
from app.schemas.admin import AgentPerformanceReportResponse

router = APIRouter()


@router.get("/agent-performance", response_model=AgentPerformanceReportResponse)
async def get_agent_performance_report(
    current_user: User = Depends(AdminRequired),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    region: Optional[str] = None,
    agent_tier: Optional[str] = None,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
):
    """Agent performance breakdown for the Reports & Analytics screen"""
    agents, total = await admin_service.get_agent_performance_report(
        db, skip, limit, region, agent_tier, period_start, period_end
    )
    return {
        "agents": agents,
        "total": total,
        "page": skip // limit + 1,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
        "period_start": period_start,
        "period_end": period_end,
    }
