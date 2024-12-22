from sqlalchemy import Column, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base, TimestampMixin
from app.models.activity import ActivityType

class Activity(Base, TimestampMixin):
    __tablename__ = "activities"

    id = Column(String, primary_key=True)
    board_id = Column(String, ForeignKey("boards.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    action = Column(Enum(ActivityType), nullable=False)
    details = Column(String, nullable=False)

    # Relationships
    board = relationship("Board", back_populates="activities")
    user = relationship("DBUser", back_populates="activities")

    def __repr__(self):
        return f"<Activity {self.id}: {self.action} on Board {self.board_id} by User {self.user_id}>"
