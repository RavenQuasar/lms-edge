from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    student_answer = Column(Text, nullable=False)
    is_correct = Column(Integer, nullable=True)
    score = Column(Float, default=0.0)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    graded = Column(Integer, default=0)
    grading_time = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="submissions")
    assignment = relationship("Assignment", back_populates="submissions")
