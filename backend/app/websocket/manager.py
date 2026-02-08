from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_connections: Dict[int, WebSocket] = {}
        self.online_users: Dict[int, dict] = {}

    async def connect(self, websocket: WebSocket, user_id: int, board_id: str = None):
        await websocket.accept()
        
        self.user_connections[user_id] = websocket
        
        if board_id:
            if board_id not in self.active_connections:
                self.active_connections[board_id] = []
            self.active_connections[board_id].append(websocket)
        
        self.online_users[user_id] = {
            "user_id": user_id,
            "board_id": board_id,
            "connected_at": None
        }
        
        await self.broadcast_online_users()
        logger.info(f"User {user_id} connected to board {board_id}")

    def disconnect(self, user_id: int, board_id: str = None):
        websocket = self.user_connections.pop(user_id, None)
        self.online_users.pop(user_id, None)
        
        if board_id and websocket:
            if board_id in self.active_connections:
                if websocket in self.active_connections[board_id]:
                    self.active_connections[board_id].remove(websocket)
                if not self.active_connections[board_id]:
                    del self.active_connections[board_id]
        
        logger.info(f"User {user_id} disconnected from board {board_id}")

    async def send_personal_message(self, message: dict, user_id: int):
        websocket = self.user_connections.get(user_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending personal message to user {user_id}: {e}")
                self.disconnect(user_id)

    async def broadcast_to_board(self, board_id: str, message: dict):
        if board_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[board_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to board {board_id}: {e}")
                    disconnected.append(connection)
            
            for connection in disconnected:
                self.active_connections[board_id].remove(connection)

    async def broadcast_online_users(self):
        online_list = list(self.online_users.values())
        message = {
            "type": "online_users",
            "data": online_list
        }
        
        for user_id, websocket in self.user_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting online users to {user_id}: {e}")

    async def broadcast_signin_status(self, signin_id: str, status: dict):
        message = {
            "type": "signin_status",
            "data": status
        }
        
        for user_id, websocket in self.user_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting signin status: {e}")

    async def handle_activity_update(self, user_id: int, activity_data: dict):
        message = {
            "type": "activity_update",
            "data": activity_data
        }
        
        for connection in self.user_connections.values():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting activity update: {e}")

    async def broadcast_quiz_result(self, assignment_id: int, result: dict):
        message = {
            "type": "quiz_result",
            "data": result
        }
        
        for connection in self.user_connections.values():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting quiz result: {e}")


manager = ConnectionManager()
