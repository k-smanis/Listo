from database import Base
from sqlalchemy import Column, Integer, String, Boolean


class Tasks(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    details = Column(String)
    priority = Column(Integer)
    is_complete = Column(Boolean, default=False)
