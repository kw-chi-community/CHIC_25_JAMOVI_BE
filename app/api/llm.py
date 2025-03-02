from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect, Body
from services import llm_results
from middleware.auth import get_current_user
from typing import Dict
from models import get_db, User
from sqlalchemy.orm import Session
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.setLevel(logging.INFO)


class LLMRequest(BaseModel):
    test_type: str
    question: str

router = APIRouter()


@router.post("/llm/results")
async def get_llm_results(request: LLMRequest):
    logger.info(f"llm_results {request.test_type}")
    logger.info(f"{request.question}")
    return llm_results(test_type=request.test_type, question=request.question)

