from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List
from datetime import datetime, timedelta
import csv
import os
from fastapi.responses import StreamingResponse
from app.core.database import get_db
from app.core.security import RoleChecker, decode_access_token
from app.models.user import User, UserRole
from app.models.attendance import Attendance
from app.models.assignment import Assignment
from app.models.submission import Submission
from app.schemas.stats import (
    UserStats,
    ClassStats,
    AssignmentStats,
    PerformanceTrend
)

router = APIRouter()

teacher_checker = RoleChecker([UserRole.ADMIN, UserRole.TEACHER])
student_checker = RoleChecker([UserRole.STUDENT])


@router.get("/class", response_model=ClassStats)
async def get_class_stats(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(teacher_checker)
):
    result = await db.execute(
        select(func.count(User.id)).where(User.role == UserRole.STUDENT)
    )
    total_students = result.scalar() or 0
    
    result = await db.execute(
        select(func.count(Assignment.id))
    )
    total_assignments = result.scalar() or 0
    
    result = await db.execute(
        select(func.avg(Submission.score))
    )
    avg_score = result.scalar() or 0.0
    
    result = await db.execute(
        select(func.count(func.distinct(Attendance.user_id)))
        .where(Attendance.login_time >= datetime.utcnow() - timedelta(days=1))
    )
    active_students = result.scalar() or 0
    
    result = await db.execute(
        select(func.count(Attendance.id))
        .where(Attendance.login_time >= datetime.utcnow() - timedelta(days=30))
    )
    total_sessions = result.scalar() or 0
    
    return ClassStats(
        total_students=total_students,
        active_students=active_students,
        total_assignments=total_assignments,
        avg_score=float(avg_score),
        total_sessions=total_sessions
    )


@router.get("/user/{user_id}", response_model=UserStats)
async def get_user_stats(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(teacher_checker)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(
        select(func.count(Attendance.id)).where(Attendance.user_id == user_id)
    )
    total_sessions = result.scalar() or 0
    
    result = await db.execute(
        select(func.sum(Attendance.session_duration)).where(Attendance.user_id == user_id)
    )
    total_duration = result.scalar() or 0
    
    result = await db.execute(
        select(func.avg(Attendance.activity_score)).where(Attendance.user_id == user_id)
    )
    avg_activity = result.scalar() or 0.0
    
    result = await db.execute(
        select(func.count(Submission.id)).where(Submission.user_id == user_id)
    )
    total_assignments = result.scalar() or 0
    
    result = await db.execute(
        select(func.count(Submission.id))
        .where(
            and_(
                Submission.user_id == user_id,
                Submission.is_correct == 1
            )
        )
    )
    correct_count = result.scalar() or 0
    
    correct_rate = (correct_count / total_assignments * 100) if total_assignments > 0 else 0.0
    
    result = await db.execute(
        select(func.count(Attendance.id))
        .where(
            and_(
                Attendance.user_id == user_id,
                Attendance.is_late == 1
            )
        )
    )
    late_count = result.scalar() or 0
    
    return UserStats(
        user_id=user_id,
        username=user.username,
        total_sessions=total_sessions,
        total_duration=total_duration,
        avg_activity_score=float(avg_activity),
        total_assignments=total_assignments,
        correct_rate=correct_rate,
        late_count=late_count
    )


@router.get("/my-stats", response_model=UserStats)
async def get_my_stats(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(student_checker)
):
    user_id = token.get("user_id")
    stats_router = APIRouter()
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(
        select(func.count(Attendance.id)).where(Attendance.user_id == user_id)
    )
    total_sessions = result.scalar() or 0
    
    result = await db.execute(
        select(func.sum(Attendance.session_duration)).where(Attendance.user_id == user_id)
    )
    total_duration = result.scalar() or 0
    
    result = await db.execute(
        select(func.avg(Assignment.points)).where(Assignment.id == Submission.assignment_id)
    )
    avg_activity = result.scalar() or 0.0
    
    result = await db.execute(
        select(func.count(Submission.id)).where(Submission.user_id == user_id)
    )
    total_assignments = result.scalar() or 0
    
    result = await db.execute(
        select(func.count(Submission.id))
        .where(
            and_(
                Submission.user_id == user_id,
                Submission.is_correct == 1
            )
        )
    )
    correct_count = result.scalar() or 0
    
    correct_rate = (correct_count / total_assignments * 100) if total_assignments > 0 else 0.0
    
    result = await db.execute(
        select(func.count(Attendance.id))
        .where(
            and_(
                Attendance.user_id == user_id,
                Attendance.is_late == 1
            )
        )
    )
    late_count = result.scalar() or 0
    
    return UserStats(
        user_id=user_id,
        username=user.username,
        total_sessions=total_sessions,
        total_duration=total_duration,
        avg_activity_score=float(avg_activity),
        total_assignments=total_assignments,
        correct_rate=correct_rate,
        late_count=late_count
    )


@router.get("/assignment/{assignment_id}", response_model=AssignmentStats)
async def get_assignment_stats(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(teacher_checker)
):
    result = await db.execute(
        select(Assignment).where(Assignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    result = await db.execute(
        select(func.count(Submission.id))
        .where(Submission.assignment_id == assignment_id)
    )
    total_submissions = result.scalar() or 0
    
    result = await db.execute(
        select(func.count(Submission.id))
        .where(
            and_(
                Submission.assignment_id == assignment_id,
                Submission.is_correct == 1
            )
        )
    )
    correct_count = result.scalar() or 0
    
    correct_rate = (correct_count / total_submissions * 100) if total_submissions > 0 else 0.0
    
    result = await db.execute(
        select(func.avg(Submission.score))
        .where(Submission.assignment_id == assignment_id)
    )
    avg_score = result.scalar() or 0.0
    
    return AssignmentStats(
        assignment_id=assignment_id,
        title=assignment.title,
        total_submissions=total_submissions,
        correct_count=correct_count,
        correct_rate=correct_rate,
        avg_score=float(avg_score)
    )


@router.get("/assignments/all", response_model=List[AssignmentStats])
async def get_all_assignments_stats(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(teacher_checker)
):
    result = await db.execute(select(Assignment))
    assignments = result.scalars().all()
    
    stats = []
    for assignment in assignments:
        result = await db.execute(
            select(func.count(Submission.id))
            .where(Submission.assignment_id == assignment.id)
        )
        total_submissions = result.scalar() or 0
        
        result = await db.execute(
            select(func.count(Submission.id))
            .where(
                and_(
                    Submission.assignment_id == assignment.id,
                    Submission.is_correct == 1
                )
            )
        )
        correct_count = result.scalar() or 0
        
        correct_rate = (correct_count / total_submissions * 100) if total_submissions > 0 else 0.0
        
        result = await db.execute(
            select(func.avg(Submission.score))
            .where(Submission.assignment_id == assignment.id)
        )
        avg_score = result.scalar() or 0.0
        
        stats.append(AssignmentStats(
            assignment_id=assignment.id,
            title=assignment.title,
            total_submissions=total_submissions,
            correct_count=correct_count,
            correct_rate=correct_rate,
            avg_score=float(avg_score)
        ))
    
    return stats


@router.get("/trend/{user_id}")
async def get_performance_trend(
    user_id: int,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(teacher_checker)
):
    from datetime import datetime, timedelta
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    result = await db.execute(
        select(
            func.date(Submission.submitted_at).label('date'),
            func.count(Submission.id).label('count'),
            func.avg(Submission.score).label('avg_score')
        )
        .where(
            and_(
                Submission.user_id == user_id,
                Submission.submitted_at >= start_date
            )
        )
        .group_by(func.date(Submission.submitted_at))
        .order_by(func.date(Submission.submitted_at))
    )
    
    trends = []
    for row in result:
        trends.append(PerformanceTrend(
            date=row.date.isoformat(),
            correct_rate=float(row.avg_score),
            assignment_count=row.count
        ))
    
    return trends


@router.get("/export/attendance")
async def export_attendance(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(teacher_checker)
):
    result = await db.execute(
        select(Attendance, User)
        .join(User, Attendance.user_id == User.id)
        .order_by(Attendance.login_time.desc())
    )
    records = result.all()
    
    output = []
    output.append(['User ID', 'Username', 'Login Time', 'Logout Time', 'Duration (seconds)', 'Activity Score', 'Is Late'])
    
    for attendance, user in records:
        output.append([
            attendance.user_id,
            user.username,
            attendance.login_time.isoformat() if attendance.login_time else '',
            attendance.logout_time.isoformat() if attendance.logout_time else '',
            str(attendance.session_duration),
            str(attendance.activity_score),
            'Yes' if attendance.is_late else 'No'
        ])
    
    filename = f"attendance_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = f"/tmp/{filename}"
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(output)
    
    return StreamingResponse(
        open(filepath, 'rb'),
        media_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@router.get("/export/assignments")
async def export_assignments(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(teacher_checker)
):
    result = await db.execute(
        select(Submission, Assignment, User)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .join(User, Submission.user_id == User.id)
        .order_by(Submission.submitted_at.desc())
    )
    records = result.all()
    
    output = []
    output.append(['User ID', 'Username', 'Assignment ID', 'Title', 'Answer', 'Is Correct', 'Score', 'Submitted At'])
    
    for submission, assignment, user in records:
        output.append([
            submission.user_id,
            user.username,
            submission.assignment_id,
            assignment.title,
            submission.student_answer,
            'Yes' if submission.is_correct else 'No',
            str(submission.score),
            submission.submitted_at.isoformat() if submission.submitted_at else ''
        ])
    
    filename = f"assignments_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = f"/tmp/{filename}"
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(output)
    
    return StreamingResponse(
        open(filepath, 'rb'),
        media_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )
