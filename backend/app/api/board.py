from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime
from app.core.database import get_db
from app.core.security import RoleChecker, decode_access_token
from app.models.user import UserRole
from app.models.board import BoardLog, BoardMessage
from app.schemas.attendance import BoardDraw, BoardMessage as BoardMessageSchema
from app.websocket import manager

router = APIRouter()

teacher_checker = RoleChecker([UserRole.ADMIN, UserRole.TEACHER])


@router.post("/draw")
async def draw_on_board(
    draw_data: BoardDraw,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(decode_access_token)
):
    payload = decode_access_token(token)
    
    board_log = BoardLog(
        board_id=draw_data.board_id,
        content={
            "action": draw_data.action,
            "x": draw_data.x,
            "y": draw_data.y,
            "color": draw_data.color,
            "size": draw_data.size,
            "points": draw_data.points
        },
        action_type=draw_data.action,
        created_by=payload.get("user_id")
    )
    db.add(board_log)
    await db.commit()
    
    await manager.broadcast_to_board(draw_data.board_id, {
        "type": "draw",
        "data": draw_data.dict()
    })
    
    return {"status": "success"}


@router.post("/clear")
async def clear_board(
    board_id: str,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(teacher_checker)
):
    await manager.broadcast_to_board(board_id, {
        "type": "clear"
    })
    return {"status": "success"}


@router.post("/message")
async def send_board_message(
    message: BoardMessageSchema,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(decode_access_token)
):
    board_message = BoardMessage(
        board_id=message.board_id,
        user_id=message.user_id,
        username=message.username,
        message=message.message,
        created_at=datetime.utcnow()
    )
    db.add(board_message)
    await db.commit()
    
    await manager.broadcast_to_board(message.board_id, {
        "type": "message",
        "data": {
            "username": message.username,
            "message": message.message
        }
    })
    
    return {"status": "success"}


@router.get("/{board_id}/messages")
async def get_board_messages(
    board_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(teacher_checker)
):
    result = await db.execute(
        select(BoardMessage)
        .where(BoardMessage.board_id == board_id)
        .order_by(BoardMessage.created_at.desc())
        .limit(limit)
    )
    messages = result.scalars().all()
    return messages
