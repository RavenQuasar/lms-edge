from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
from app.models.assignment import AssignmentType


class AssignmentBase(BaseModel):
    title: str
    content: Optional[str] = None
    assignment_type: AssignmentType
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    points: int = 10
    due_date: Optional[datetime] = None


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    points: Optional[int] = None
    due_date: Optional[datetime] = None
    is_active: Optional[int] = None


class AssignmentResponse(AssignmentBase):
    id: int
    created_by: int
    created_at: datetime
    is_active: int

    class Config:
        from_attributes = True


class SubmissionCreate(BaseModel):
    assignment_id: int
    student_answer: str


class SubmissionResponse(BaseModel):
    id: int
    user_id: int
    assignment_id: int
    student_answer: str
    is_correct: Optional[int] = None
    score: float
    submitted_at: datetime
    graded: int

    class Config:
        from_attributes = True


class QuizResult(BaseModel):
    assignment_id: int
    total_submissions: int
    correct_count: int
    avg_score: float
