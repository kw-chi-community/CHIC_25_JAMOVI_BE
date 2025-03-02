from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Union

from models import get_db
from services.statistics_results import get_statistical_test_result
from schemas.results import (
    ANOVAResult,
    PairedTTestResultResponse,
    IndependentTTestResultResponse,
    OneSampleTTestResultResponse
)

router = APIRouter(prefix="/results", tags=["Statistics"])


# 통합 응답 모델
StatisticalResult = Union[
    ANOVAResult,
    PairedTTestResultResponse,
    IndependentTTestResultResponse,
    OneSampleTTestResultResponse
]

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


@router.get("/{test_id}", response_model=StatisticalResult)
async def get_statistical_result(
        test_id: int,
        db: Session = Depends(get_db)
):
    result = get_statistical_test_result(test_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="Test not found")
    return result


# 헬퍼 함수
def parse_group_stats(result, prefix: str) -> Dict[str, float]:
    return {
        "mean": getattr(result, f"stats_{prefix}_mean"),
        "sd": getattr(result, f"stats_{prefix}_sd"),
        "n": getattr(result, f"stats_{prefix}_n"),
        "min": getattr(result, f"stats_{prefix}_min"),
        "max": getattr(result, f"stats_{prefix}_max")
    }


def parse_diff_stats(result) -> Dict[str, float]:
    return {
        "mean": result.stats_diff_mean,
        "sd": result.stats_diff_sd,
        "n": result.stats_diff_n,
        "min": result.stats_diff_min,
        "max": result.stats_diff_max
    }


def parse_sample_stats(result) -> Dict[str, float]:
    return {
        "mean": result.stats_mean,
        "median": result.stats_median,
        "sd": result.stats_sd,
        "q1": result.stats_q1,
        "q3": result.stats_q3
    }