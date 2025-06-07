from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True) 
    username = Column(String(50), nullable=False)  
    email = Column(String(255), nullable=False)    
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default='user')
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    customer = relationship("Customer", back_populates="users")
    user_achievements = relationship(
        "Achievement",
        secondary="user_achievements",
        back_populates="users"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, customer_id={self.customer_id}, email='{self.email}', username='{self.username}')>"