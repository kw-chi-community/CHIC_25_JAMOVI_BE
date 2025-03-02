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

    return {**test.__dict__, **result.__dict__}

def _handle_paired_ttest_result(test: StatisticalTest, db: Session) -> Optional[PairedTTestResultResponse]:
    result = db.query(PairedTTestResult).filter(
        PairedTTestResult.statistical_test_id == test.id
    ).first()

    if not result:
        return None

    return {**test.__dict__, **result.__dict__}

def _handle_independent_ttest_result(test: StatisticalTest, db: Session) -> Optional[IndependentTTestResultResponse]:
    result = db.query(IndependentTTestResult).filter(
        IndependentTTestResult.statistical_test_id == test.id
    ).first()

    if not result:
        return None

    return {**test.__dict__, **result.__dict__}

def _handle_one_sample_ttest_result(test: StatisticalTest, db: Session) -> Optional[OneSampleTTestResultResponse]:
    result = db.query(OneSampleTTestResult).filter(
        OneSampleTTestResult.statistical_test_id == test.id
    ).first()

    if not result:
        return None

    return {**test.__dict__, **result.__dict__}
