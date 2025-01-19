from fastapi import APIRouter
from services import llm_results
from utils import logger

router = APIRouter()

router = APIRouter(prefix="/test")

@router.get("/")
async def test():
    logger.info("test")
    return "test"

@router.get("/test")
async def test():
    logger.info("test")
    return "test"

@router.get("/output/results")
async def output_results():
    logger.info("output_results")
    return llm_results("What do you know about Korea?")
