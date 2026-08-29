from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import AdminRequired
from app.models.user import User
from app.services.admin_service import admin_service
from app.schemas.admin import PlatformSettingsResponse, PlatformSettingsUpdate

router = APIRouter()


@router.get("/", response_model=PlatformSettingsResponse)
async def get_platform_settings(
    current_user: User = Depends(AdminRequired),
    db: AsyncSession = Depends(get_db)
):
    """Get the current Referral Program Settings"""
    settings = await admin_service.get_platform_settings(db)
    return settings


@router.put("/", response_model=PlatformSettingsResponse)
async def update_platform_settings(
    data: PlatformSettingsUpdate,
    current_user: User = Depends(AdminRequired),
    db: AsyncSession = Depends(get_db)
):
    """Update the Referral Program Settings ('Save Changes' action)"""
    settings = await admin_service.update_platform_settings(db, data)
    return settings
