from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import AdminRequired
from app.models.user import User
from app.services.admin_service import admin_service
from app.schemas.admin import AdminDashboardStatsResponse

router = APIRouter()


@router.get("/stats", response_model=AdminDashboardStatsResponse)
async def get_admin_dashboard_stats(
    current_user: User = Depends(AdminRequired),
    db: AsyncSession = Depends(get_db)
):
    """Get platform-wide overview statistics for the admin dashboard"""
    stats = await admin_service.get_dashboard_stats(db)
    return stats
