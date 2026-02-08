from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import decode_access_token
from app.websocket import manager
from app.models.user import User
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    board_id: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    user_id = payload.get("user_id")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        await websocket.close(code=4002, reason="User not found")
        return
    
    await manager.connect(websocket, user_id, board_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                message_type = message.get("type")
                message_data = message.get("data", {})
                
                if message_type == "ping":
                    await websocket.send_json({"type": "pong"})
                
                elif message_type == "activity_update":
                    activity_data = {
                        "user_id": user_id,
                        "username": user.username,
                        "is_active": message_data.get("is_active", True),
                        "visible": message_data.get("visible", True)
                    }
                    await manager.handle_activity_update(user_id, activity_data)
                
                elif message_type == "board_draw":
                    if board_id:
                        draw_data = {
                            "board_id": board_id,
                            "action": message_data.get("action"),
                            "x": message_data.get("x"),
                            "y": message_data.get("y"),
                            "color": message_data.get("color"),
                            "size": message_data.get("size"),
                            "points": message_data.get("points")
                        }
                        await manager.broadcast_to_board(board_id, {
                            "type": "draw",
                            "data": draw_data
                        })
                
                elif message_type == "board_message":
                    if board_id:
                        message_content = {
                            "board_id": board_id,
                            "user_id": user_id,
                            "username": user.username,
                            "message": message_data.get("message")
                        }
                        await manager.broadcast_to_board(board_id, {
                            "type": "message",
                            "data": message_content
                        })
                
                elif message_type == "board_clear":
                    if board_id:
                        await manager.broadcast_to_board(board_id, {
                            "type": "clear"
                        })
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from user {user_id}")
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
            except Exception as e:
                logger.error(f"Error processing message from user {user_id}: {e}")
                await websocket.send_json({"type": "error", "message": str(e)})
                
    except WebSocketDisconnect:
        manager.disconnect(user_id, board_id)
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id, board_id)
