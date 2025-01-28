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
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    current_user=Depends(get_current_user)
    logger.info(f"current_user: {current_user}")
    user = db.query(User).filter(User.id == current_user["user"]).first()
    try:
        await websocket.accept()
        connected_clients[user] = websocket
        
        logger.info(f"user {user} connected")
        
        try:
            while True:
                data = await websocket.receive_text()
                logger.info(f"{user}: {data}")
                
                response = f"server received: {data}"
                await websocket.send_text(response)
                
        except WebSocketDisconnect:
            connected_clients.pop(user, None)
            logger.info(f"{user} disconnected")
            
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        connected_clients.pop(user, None)

@router.get("/test")
async def test():
    logger.info("test")
    return "test"

@router.get("/test/output/results")
async def output_results():
    logger.info("output_results")
    return llm_results("What do you know about Korea?")

