from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class UserStats(BaseModel):
    user_id: int
    username: str
    total_sessions: int
    total_duration: int
    avg_activity_score: float
    total_assignments: int
    correct_rate: float
    late_count: int


class ClassStats(BaseModel):
    total_students: int
    active_students: int
    total_assignments: int
    avg_score: float
    total_sessions: int


class AssignmentStats(BaseModel):
    assignment_id: int
    title: str
    total_submissions: int
    correct_count: int
    correct_rate: float
    avg_score: float


class PerformanceTrend(BaseModel):
    date: str
    correct_rate: float
    assignment_count: int


class SystemInfo(BaseModel):
    cpu_usage: float
    cpu_count: int
    memory_usage: float
    memory_total: float
    disk_usage: float
    disk_total: float
    temperature: Optional[float] = None
    uptime: str


class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    message: str
    user_id: Optional[int] = None


class ExportRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    format: str = "csv"
    type: str = "attendance"
