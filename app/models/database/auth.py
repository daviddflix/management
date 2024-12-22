from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class DBToken(Base):
    __tablename__ = "auth_tokens"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    access_token = Column(String, nullable=False, unique=True)
    refresh_token = Column(String, unique=True)
    token_type = Column(String, nullable=False, default="bearer")
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())

    # Relationships
    user = relationship("DBUser", back_populates="tokens")
