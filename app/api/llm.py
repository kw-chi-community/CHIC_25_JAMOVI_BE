from fastapi import APIRouter
from services import llm_results, llm_conclusions
import logging
from schemas import llmResultRequest, llmConclusionRequest
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from models.statistical_test import StatisticalTest
from models import get_db

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
    output = llm_results(
        test_type=request.test_type,
        question=request.question,
        statistical_test_id=request.statistical_test_id
    )
    logger.info(f"llm_results {output}")
    return output

@router.post("/conclusion")
async def get_llm_conclusion(request: llmConclusionRequest):
    logger.info(f"llm_conclusion {request.test_type}")
    logger.info(f"{request.experimental_design}")
    logger.info(f"{request.subject_info}")
    logger.info(f"{request.question}")
    logger.info(f"{request.statistical_test_id}")
    output = llm_conclusions(test_type=request.test_type, experimental_design=request.experimental_design, subject_info=request.subject_info, question=request.question, statistical_test_id=request.statistical_test_id)
    logger.info(f"llm_conclusion {output}")
    return output

@router.get("/output/{test_id}")
async def get_test_results_and_conclusion(test_id: int, db: Session = Depends(get_db)):
    logger.info(f"Getting results and conclusion for test ID: {test_id}")
    
    statistical_test = db.query(StatisticalTest).filter(StatisticalTest.id == test_id).first()
    
    if not statistical_test:
        logger.error(f"Statistical test with ID {test_id} not found")
        raise HTTPException(status_code=404, detail="Statistical test not found")
    
    return {
        "results": statistical_test.results,
        "conclusion": statistical_test.conclusion
    }