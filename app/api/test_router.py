from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from services import llm_results
from utils import logger
from middleware.auth import get_current_user
from typing import Dict
from models import get_db, User
from sqlalchemy.orm import Session
router = APIRouter()

connected_clients: Dict[str, WebSocket] = {}

@router.websocket("/ws/test")
async def websocket_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    current_user = await get_current_user(websocket=websocket)
    if not current_user:
        return
    
    try:
        await websocket.accept()
        
        logger.info(f"current_user: {current_user}")
        user = db.query(User).filter(User.id == current_user["user"]).first()
        
        if not user:
            await websocket.close(code=4003, reason="User not found")
            return
            
        connected_clients[str(user.id)] = websocket
        logger.info(f"user {user.id} connected")
        
        try:
            while True:
                data = await websocket.receive_text()
                logger.info(f"User {user.id}: {data}")
                
                response = f"server received: {data}"
                await websocket.send_text(response)
                
        except WebSocketDisconnect:
            connected_clients.pop(str(user.id), None)
            logger.info(f"User {user.id} disconnected")
            
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.close(code=4000)
        except:
            pass
        if user:
            connected_clients.pop(str(user.id), None)

@router.get("/test")
async def test():
    logger.info("test")
    return "test"

@router.get("/test/output/results")
async def output_results():
    logger.info("output_results")
    return llm_results("What do you know about Korea?")

