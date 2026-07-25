from sqlalchemy import Column, String, JSON, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(String(255), nullable=False)
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(String(500))

    # Relationships
    user = relationship("User", backref="audit_logs")