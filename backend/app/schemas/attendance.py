from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class AttendanceResponse(BaseModel):
    id: int
    user_id: int
    login_time: datetime
    logout_time: Optional[datetime] = None
    activity_score: float
    session_duration: int
    is_late: int

    class Config:
        from_attributes = True


class AttendanceCreate(BaseModel):
    user_id: int


class SigninRequest(BaseModel):
    duration_minutes: int = 5


class SigninResponse(BaseModel):
    signin_id: str
    expires_at: datetime
    active: bool


class SigninRecord(BaseModel):
    user_id: int
    username: str
    signed_in_at: Optional[datetime] = None


class BoardDraw(BaseModel):
    board_id: str
    action: str
    x: Optional[float] = None
    y: Optional[float] = None
    color: Optional[str] = "#000000"
    size: Optional[int] = 2
    points: Optional[List[List[float]]] = None


class BoardSnapshot(BaseModel):
    board_id: str
    snapshot_path: str


class BoardMessage(BaseModel):
    board_id: str
    user_id: int
    username: str
    message: str
    created_at: datetime


class OnlineUser(BaseModel):
    user_id: int
    username: str
    role: str
    avatar: str
    last_seen: datetime
