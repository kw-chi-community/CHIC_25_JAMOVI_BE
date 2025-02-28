from typing import Dict, Optional, Union
from sqlalchemy.orm import Session

from models import (
    StatisticalTest,
    OneWayANOVAResult,
    PairedTTestResult,
    IndependentTTestResult,
    OneSampleTTestResult
)
from schemas.results import (
    ANOVAResult,
    PairedTTestResultResponse,
    IndependentTTestResultResponse,
    OneSampleTTestResultResponse
)

def get_statistical_test_result(test_id: int, db: Session) -> Optional[Union[
    ANOVAResult,
    PairedTTestResultResponse,
    IndependentTTestResultResponse,
    OneSampleTTestResultResponse
]]:
    test = db.query(StatisticalTest).filter(
        StatisticalTest.id == test_id
    ).first()

    if not test:
        return None

    if test.test_method == "OneWayANOVA":
        return _handle_anova_result(test, db)
    elif test.test_method == "PairedTTest":
        return _handle_paired_ttest_result(test, db)
    elif test.test_method == "IndependentTTest":
        return _handle_independent_ttest_result(test, db)
    elif test.test_method == "OneSampleTTest":
        return _handle_one_sample_ttest_result(test, db)
    
    return None

def _handle_anova_result(test: StatisticalTest, db: Session) -> Optional[ANOVAResult]:
    result = db.query(OneWayANOVAResult).filter(
        OneWayANOVAResult.statistical_test_id == test.id
    ).first()
    
    if not result:
        return None

    return ANOVAResult(
        **test.__dict__,
        between_df=result.between_df,
        between_f=result.between_f,
        total_mean=result.total_mean,
        group_stats=result.group_descriptive_stats,
        image_url=test.image_url
    )

def _handle_paired_ttest_result(test: StatisticalTest, db: Session) -> Optional[PairedTTestResultResponse]:
    result = db.query(PairedTTestResult).filter(
        PairedTTestResult.statistical_test_id == test.id
    ).first()

    if not result:
        return None

    return PairedTTestResultResponse(
        **test.__dict__,
        t_statistic=result.t_statistic,
        df=result.df,
        p_value=result.p_value,
        group1_stats=parse_group_stats(result, "group1"),
        group2_stats=parse_group_stats(result, "group2"),
        diff_stats=parse_diff_stats(result)
    )

def _handle_independent_ttest_result(test: StatisticalTest, db: Session) -> Optional[IndependentTTestResultResponse]:
    result = db.query(IndependentTTestResult).filter(
        IndependentTTestResult.statistical_test_id == test.id
    ).first()

    if not result:
        return None

    return IndependentTTestResultResponse(
        **test.__dict__,
        t_statistic=result.t_statistic,
        df=result.df,
        p_value=result.p_value,
        group1_stats=parse_group_stats(result, "group1"),
        group2_stats=parse_group_stats(result, "group2")
    )

def _handle_one_sample_ttest_result(test: StatisticalTest, db: Session) -> Optional[OneSampleTTestResultResponse]:
    result = db.query(OneSampleTTestResult).filter(
        OneSampleTTestResult.statistical_test_id == test.id
    ).first()

    if not result:
        return None

    return OneSampleTTestResultResponse(
        **test.__dict__,
        t_statistic=result.t_statistic,
        df=result.df,
        p_value=result.p_value,
        sample_stats=parse_sample_stats(result),
        mu=result.mu
    )

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