# achievements.py

from sqlalchemy import Column, Integer, String, Float, DateTime, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

# Association table for many-to-many User <-> Achievement relationship
user_achievements = Table(
    "user_achievements",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.id"), primary_key=True),
    Column("achievement_id", Integer, ForeignKey("achievements.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Column("status", String(50), nullable=False, default="pending"),
    Column("due_date", DateTime(timezone=True), nullable=True)
)

class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    point_value = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    duration = Column(Integer, nullable=False)  # Duration in minutes
    frequency = Column(String(50), nullable=False)

    # Relationships
    users = relationship(
        "User",
        secondary="user_achievements",
        back_populates="user_achievements"
    )
