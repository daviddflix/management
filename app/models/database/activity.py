from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.activity import ActivityType

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    board_id = Column(Integer, ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(SQLEnum(ActivityType), nullable=False)
    details = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.now(), nullable=False)

    # Relationships
    board = relationship("Board", back_populates="activities")
    user = relationship("User", back_populates="activities")

    def __repr__(self):
        return f"<Activity {self.id}: {self.action} on Board {self.board_id} by User {self.user_id}>"
