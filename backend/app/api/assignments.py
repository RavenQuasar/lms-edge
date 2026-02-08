from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from app.core.database import get_db
from app.core.security import RoleChecker, decode_access_token
from app.models.user import UserRole
from app.models.assignment import Assignment, AssignmentType
from app.models.submission import Submission
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentUpdate,
    AssignmentResponse,
    SubmissionCreate,
    SubmissionResponse,
    QuizResult
)

router = APIRouter()

teacher_checker = RoleChecker([UserRole.ADMIN, UserRole.TEACHER])
student_checker = RoleChecker([UserRole.STUDENT])


@router.post("/", response_model=AssignmentResponse)
async def create_assignment(
    assignment: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(teacher_checker)
):
    payload = decode_access_token(token)
    db_assignment = Assignment(
        title=assignment.title,
        content=assignment.content,
        assignment_type=assignment.assignment_type,
        options=assignment.options,
        correct_answer=assignment.correct_answer,
        points=assignment.points,
        due_date=assignment.due_date,
        created_by=payload.get("user_id")
    )
    db.add(db_assignment)
    await db.commit()
    await db.refresh(db_assignment)
    return db_assignment


@router.get("/", response_model=List[AssignmentResponse])
async def get_assignments(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(teacher_checker)
):
    query = select(Assignment)
    if active_only:
        query = query.where(Assignment.is_active == 1)
    query = query.order_by(Assignment.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    assignments = result.scalars().all()
    return assignments


@router.get("/student", response_model=List[AssignmentResponse])
async def get_student_assignments(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(student_checker)
):
    query = select(Assignment).where(Assignment.is_active == 1)
    query = query.order_by(Assignment.created_at.desc())
    result = await db.execute(query)
    assignments = result.scalars().all()
    return assignments


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(teacher_checker)
):
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    return assignment


@router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: int,
    assignment_update: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(teacher_checker)
):
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    db_assignment = result.scalar_one_or_none()
    if db_assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    if assignment_update.title is not None:
        db_assignment.title = assignment_update.title
    if assignment_update.content is not None:
        db_assignment.content = assignment_update.content
    if assignment_update.points is not None:
        db_assignment.points = assignment_update.points
    if assignment_update.due_date is not None:
        db_assignment.due_date = assignment_update.due_date
    if assignment_update.is_active is not None:
        db_assignment.is_active = assignment_update.is_active
    
    await db.commit()
    await db.refresh(db_assignment)
    return db_assignment


@router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(teacher_checker)
):
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    db_assignment = result.scalar_one_or_none()
    if db_assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    await db.delete(db_assignment)
    await db.commit()
    return {"message": "Assignment deleted successfully"}


@router.post("/{assignment_id}/submit", response_model=SubmissionResponse)
async def submit_assignment(
    assignment_id: int,
    submission: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(student_checker)
):
    payload = decode_access_token(token)
    
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    db_submission = Submission(
        user_id=payload.get("user_id"),
        assignment_id=assignment_id,
        student_answer=submission.student_answer
    )
    
    if assignment.assignment_type != AssignmentType.SHORT_ANSWER:
        is_correct = submission.student_answer == assignment.correct_answer
        db_submission.is_correct = 1 if is_correct else 0
        db_submission.score = assignment.points if is_correct else 0
        db_submission.graded = 1
    
    db.add(db_submission)
    await db.commit()
    await db.refresh(db_submission)
    return db_submission


@router.get("/{assignment_id}/submissions", response_model=List[SubmissionResponse])
async def get_submissions(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(teacher_checker)
):
    result = await db.execute(
        select(Submission)
        .where(Submission.assignment_id == assignment_id)
        .order_by(Submission.submitted_at.desc())
    )
    submissions = result.scalars().all()
    return submissions


@router.get("/{assignment_id}/quiz-result", response_model=QuizResult)
async def get_quiz_result(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(teacher_checker)
):
    result = await db.execute(
        select(func.count(Submission.id))
        .where(Submission.assignment_id == assignment_id)
    )
    total_submissions = result.scalar() or 0
    
    result = await db.execute(
        select(func.count(Submission.id))
        .where(
            Submission.assignment_id == assignment_id,
            Submission.is_correct == 1
        )
    )
    correct_count = result.scalar() or 0
    
    result = await db.execute(
        select(func.avg(Submission.score))
        .where(Submission.assignment_id == assignment_id)
    )
    avg_score = result.scalar() or 0.0
    
    return QuizResult(
        assignment_id=assignment_id,
        total_submissions=total_submissions,
        correct_count=correct_count,
        avg_score=float(avg_score)
    )
