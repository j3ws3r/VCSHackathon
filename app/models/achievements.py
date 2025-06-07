from sqlalchemy import Column, Integer, String, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

user_achievements = Table(
    "user_achievements",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("achievement_id", Integer, ForeignKey("achievements.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Column("status", String(50), nullable=False, default="pending"),
    Column("due_date", DateTime(timezone=True), nullable=True)
)

class Achievement(Base):
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    point_value = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    duration = Column(Integer, nullable=False)
    frequency = Column(String(50), nullable=False)
    
    users = relationship(
        "User",
        secondary="user_achievements",
        back_populates="user_achievements"
    )