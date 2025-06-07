from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class User(Base):
    """
    SQLAlchemy model for the users table.

    Attributes:
        id (int): Unique identifier for the user.
        email (str): User's email address, must be unique.
        pass_hash (str): Hashed password.
        salt (str): Salt used for hashing the password.
        full_name (str): User's full name.
        created (datetime): Timestamp when the user was created.
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    pass_hash = Column(String(255), nullable=False)
    salt = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    created = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', full_name='{self.full_name}')>"