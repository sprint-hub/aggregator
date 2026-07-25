from sqlalchemy import Column, String, JSON, Boolean
from app.models.base import BaseModel


class SystemSetting(BaseModel):
    __tablename__ = "system_settings"

    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(JSON, nullable=False)
    category = Column(String(100))
    description = Column(String(500))
    is_public = Column(Boolean, default=False)