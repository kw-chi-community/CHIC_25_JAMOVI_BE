from fastapi import APIRouter
from services import llm_results
import logging
from schemas import llmResultRequest

logger = logging.getLogger(__name__)

formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.setLevel(logging.INFO)


router = APIRouter()


@router.post("/llm/results")
async def get_llm_results(request: llmResultRequest):
    logger.info(f"llm_results {request.test_type}")
    logger.info(f"{request.question}")
    return llm_results(test_type=request.test_type, question=request.question)

