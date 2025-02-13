import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from services import llm_results
from schemas import ExperimentData

import logging

logger = logging.getLogger(__name__)

formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.setLevel(logging.INFO)



router = APIRouter(prefix="/analyze")

@router.post("/results")
async def analyze_results(data: ExperimentData):
    logger.info("/analyze/results")
    logger.info(f"data: {data}")

    statistics_result = data.statistics_result #json
    statistical_method = data.statistical_method #str
    experiment_design = data.experiment_design #str
    subject_info = data.subject_info #str

    # 일단 이렇게 구성할게요
    # 아래 프롬프트를 작성해주신 프롬프트로 수정하는 것이 필요해요.
    # 또한, system prompt와 예시들도 수정이 필요해요. (services/prompt 참고)

    prompt = f"""
    ### 실험 설계 방식
    {experiment_design}

    ### 통계 방법
    {statistical_method}

    ### 피험자 정보
    {subject_info}

    ### 통계 결과
    {statistics_result}
    """
    

    result = llm_results(prompt)

    return result

