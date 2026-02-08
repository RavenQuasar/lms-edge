from sqlalchemy import Column, Integer, Text, DateTime, String, JSON, ForeignKey
from datetime import datetime
from app.core.database import Base


class BoardLog(Base):
    __tablename__ = "board_logs"

    id = Column(Integer, primary_key=True, index=True)
    board_id = Column(String(50), index=True, nullable=False)
    content = Column(JSON, nullable=False)
    action_type = Column(String(50), default="draw")
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    snapshot_path = Column(String(255), nullable=True)


class BoardMessage(Base):
    __tablename__ = "board_messages"

    id = Column(Integer, primary_key=True, index=True)
    board_id = Column(String(50), index=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    username = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
