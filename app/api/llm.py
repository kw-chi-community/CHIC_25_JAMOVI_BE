from fastapi import APIRouter
from services import llm_results, llm_conclusions
import logging
from schemas import llmResultRequest, llmConclusionRequest

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


@router.post("/results")
async def get_llm_results(request: llmResultRequest):
    logger.info(f"llm_results {request.test_type}")
    logger.info(f"{request.question}")
    return llm_results(
        test_type=request.test_type,
        question=request.question,
        statistical_test_id=request.statistical_test_id
        )

@router.post("/conclusion")
async def get_llm_conclusion(request: llmConclusionRequest):
    logger.info(f"llm_conclusion {request.test_type}")
    logger.info(f"{request.experimental_design}")
    logger.info(f"{request.subject_info}")
    logger.info(f"{request.question}")
    return llm_conclusions(test_type=request.test_type, experimental_design=request.experimental_design, subject_info=request.subject_info, question=request.question)