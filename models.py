from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey


class Tasks(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    details = Column(String)
    priority = Column(Integer)
    is_complete = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String)
