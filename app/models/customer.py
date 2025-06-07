from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class Customer(Base):
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(255), unique=True, nullable=False)
    company_email = Column(String(255), unique=True, nullable=False)
    company_phone = Column(String(50), nullable=True)
    company_address = Column(Text, nullable=True)
    subscription_plan = Column(String(50), default='basic') 
    max_users = Column(Integer, default=50) 
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    billing_email = Column(String(255), nullable=True)
    subscription_expires_at = Column(DateTime, nullable=True)
    
    admin_first_name = Column(String(100), nullable=False)
    admin_last_name = Column(String(100), nullable=False)
    admin_email = Column(String(255), nullable=False)
    admin_phone = Column(String(50), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    users = relationship("User", back_populates="customer", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Customer(id={self.id}, company_name='{self.company_name}', admin_email='{self.admin_email}')>"
    
    @property
    def user_count(self):
        """Get current number of users for this customer"""
        return len(self.users) if self.users else 0
    
    @property
    def can_add_users(self):
        """Check if customer can add more users"""
        return self.user_count < self.max_users
    
    @property
    def is_subscription_active(self):
        """Check if subscription is still active"""
        if not self.subscription_expires_at:
            return True  
        return datetime.utcnow() < self.subscription_expires_at