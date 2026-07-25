from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid


class BaseModel(Base):
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    