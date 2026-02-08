from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from datetime import datetime, timedelta
import uuid
from app.core.database import get_db
from app.core.security import RoleChecker, decode_access_token
from app.models.user import UserRole
from app.models.attendance import Attendance
from app.schemas.attendance import (
    AttendanceResponse,
    SigninRequest,
    SigninResponse,
    SigninRecord
)

router = APIRouter()

teacher_checker = RoleChecker([UserRole.ADMIN, UserRole.TEACHER])

active_signins = {}


@router.post("/signin", response_model=SigninResponse)
async def start_signin(
    request: SigninRequest,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(teacher_checker)
):
    signin_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=request.duration_minutes)
    
    active_signins[signin_id] = {
        "expires_at": expires_at,
        "active": True,
        "duration_minutes": request.duration_minutes
    }
    
    return SigninResponse(
        signin_id=signin_id,
        expires_at=expires_at,
        active=True
    )


@router.post("/signin/{signin_id}")
async def sign_in(
    signin_id: str,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(decode_access_token)
):
    if signin_id not in active_signins:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sign-in session not found"
        )
    
    signin = active_signins[signin_id]
    if not signin["active"] or signin["expires_at"] < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sign-in session has expired"
        )
    
    user_id = token.get("user_id")
    now = datetime.utcnow()
    
    result = await db.execute(
        select(Attendance)
        .where(Attendance.user_id == user_id)
        .order_by(Attendance.login_time.desc())
    )
    last_attendance = result.scalar_one_or_none()
    
    if last_attendance and last_attendance.logout_time is None:
        last_attendance.logout_time = now
        last_attendance.session_duration = int((now - last_attendance.login_time).total_seconds())
        await db.commit()
    
    is_late = 1 if (signin["expires_at"] - now).total_seconds() < (signin["duration_minutes"] * 60 * 0.8) else 0
    
    attendance = Attendance(
        user_id=user_id,
        login_time=now,
        activity_score=100.0,
        is_late=is_late
    )
    db.add(attendance)
    await db.commit()
    
    return {"message": "Signed in successfully"}


@router.get("/signin/{signin_id}/records", response_model=List[SigninRecord])
async def get_signin_records(
    signin_id: str,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(teacher_checker)
):
    from app.models.user import User
    
    if signin_id not in active_signins:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sign-in session not found"
        )
    
    signin_start = active_signins[signin_id]["expires_at"] - timedelta(
        minutes=active_signins[signin_id]["duration_minutes"]
    )
    
    result = await db.execute(
        select(Attendance, User)
        .join(User, Attendance.user_id == User.id)
        .where(Attendance.login_time >= signin_start)
    )
    records = result.all()
    
    return [
        SigninRecord(
            user_id=attendance.user_id,
            username=user.username,
            signed_in_at=attendance.login_time
        )
        for attendance, user in records
    ]


@router.post("/logout")
async def logout(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(decode_access_token)
):
    user_id = token.get("user_id")
    now = datetime.utcnow()
    
    result = await db.execute(
        select(Attendance)
        .where(Attendance.user_id == user_id)
        .order_by(Attendance.login_time.desc())
    )
    attendance = result.scalar_one_or_none()
    
    if attendance and attendance.logout_time is None:
        attendance.logout_time = now
        attendance.session_duration = int((now - attendance.login_time).total_seconds())
        await db.commit()
    
    return {"message": "Logged out successfully"}


@router.get("/records", response_model=List[AttendanceResponse])
async def get_attendance_records(
    user_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(teacher_checker)
):
    query = select(Attendance)
    if user_id:
        query = query.where(Attendance.user_id == user_id)
    query = query.order_by(Attendance.login_time.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    attendances = result.scalars().all()
    return attendances


@router.get("/my-records", response_model=List[AttendanceResponse])
async def get_my_attendance_records(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(decode_access_token)
):
    user_id = token.get("user_id")
    query = select(Attendance).where(Attendance.user_id == user_id)
    query = query.order_by(Attendance.login_time.desc())
    result = await db.execute(query)
    attendances = result.scalars().all()
    return attendances
