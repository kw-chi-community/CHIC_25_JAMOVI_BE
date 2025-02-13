from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Union
from typing import Optional, Dict, Any, List # noqa

from models import (
    StatisticalTest,
    OneWayANOVAResult,
    PairedTTestResult,
    IndependentTTestResult,
    OneSampleTTestResult,
    get_db
)

router = APIRouter(prefix="/results", tags=["Statistics"])


# 공통 응답 모델
class BaseStatisticalResult(BaseModel):
    test_method: str
    confidence_interval: float
    hypothesis: str
    effect_size: Optional[str] = None
    normality_satisfied: bool
    conclusion: Optional[str]


# ANOVA 결과 모델
class ANOVAResult(BaseStatisticalResult):
    between_df: int
    between_f: float
    total_mean: float
    group_stats: Dict[str, Dict[str, float]]
    image_url: Optional[str]


# Paired T-Test 결과 모델
class PairedTTestResultResponse(BaseStatisticalResult):
    t_statistic: float
    df: int
    p_value: float
    group1_stats: Dict[str, float]
    group2_stats: Dict[str, float]
    diff_stats: Dict[str, float]


# Independent T-Test 결과 모델
class IndependentTTestResultResponse(BaseStatisticalResult):
    t_statistic: float
    df: int
    p_value: float
    group1_stats: Dict[str, float]
    group2_stats: Dict[str, float]


# One Sample T-Test 결과 모델
class OneSampleTTestResultResponse(BaseStatisticalResult):
    t_statistic: float
    df: int
    p_value: float
    sample_stats: Dict[str, float]
    mu: float


# 통합 응답 모델
StatisticalResult = Union[
    ANOVAResult,
    PairedTTestResultResponse,
    IndependentTTestResultResponse,
    OneSampleTTestResultResponse
]


@router.get("/{test_id}", response_model=StatisticalResult)
async def get_statistical_result(
        test_id: int,
        db: Session = Depends(get_db)
):
    # 기본 테스트 정보 조회
    test = db.query(StatisticalTest).filter(
        StatisticalTest.id == test_id
    ).first()

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # 테스트 유형별 결과 처리
    if test.test_method == "OneWayANOVA":
        result = db.query(OneWayANOVAResult).filter(
            OneWayANOVAResult.statistical_test_id == test_id
        ).first()
        if not result:
            raise HTTPException(status_code=404, detail="ANOVA result not found")

        return {
            **test.__dict__,
            "between_df": result.between_df,
            "between_f": result.between_f,
            "total_mean": result.total_mean,
            "group_stats": result.group_descriptive_stats,
            "image_url": test.image_url
        }

    elif test.test_method == "PairedTTest":
        result = db.query(PairedTTestResult).filter(
            PairedTTestResult.statistical_test_id == test_id
        ).first()

        # 결과 파싱
        return PairedTTestResultResponse(
            **test.__dict__,
            t_statistic=result.t_statistic,
            df=result.df,
            p_value=result.p_value,
            group1_stats=parse_group_stats(result, "group1"),
            group2_stats=parse_group_stats(result, "group2"),
            diff_stats=parse_diff_stats(result)
        )

    elif test.test_method == "IndependentTTest":
        result = db.query(IndependentTTestResult).filter(
            IndependentTTestResult.statistical_test_id == test_id
        ).first()

        return IndependentTTestResultResponse(
            **test.__dict__,
            t_statistic=result.t_statistic,
            df=result.df,
            p_value=result.p_value,
            group1_stats=parse_group_stats(result, "group1"),
            group2_stats=parse_group_stats(result, "group2")
        )

    elif test.test_method == "OneSampleTTest":
        result = db.query(OneSampleTTestResult).filter(
            OneSampleTTestResult.statistical_test_id == test_id
        ).first()

        return OneSampleTTestResultResponse(
            **test.__dict__,
            t_statistic=result.t_statistic,
            df=result.df,
            p_value=result.p_value,
            sample_stats=parse_sample_stats(result),
            mu=result.mu
        )

    else:
        raise HTTPException(status_code=400, detail="Unsupported test type")


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