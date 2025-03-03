from pydantic import BaseModel
from typing import Optional, Dict, Union

class BaseStatisticalResult(BaseModel):
    test_method: str
    confidence_interval: float
    hypothesis: str
    effect_size: Optional[str] = None
    normality_satisfied: bool
    conclusion: Optional[str]

class ANOVAResult(BaseStatisticalResult):
    between_df: int
    between_f: float
    total_mean: float
    group_stats: Dict[str, Dict[str, float]]
    image_url: Optional[str]

class PairedTTestResultResponse(BaseStatisticalResult):
    t_statistic: float
    df: int
    p_value: float
    group1_stats: Dict[str, float]
    group2_stats: Dict[str, float]
    diff_stats: Dict[str, float]

class IndependentTTestResultResponse(BaseStatisticalResult):
    t_statistic: float
    df: int
    p_value: float
    group1_stats: Dict[str, float]
    group2_stats: Dict[str, float]

class OneSampleTTestResultResponse(BaseStatisticalResult):
    t_statistic: float
    df: int
    p_value: float
    sample_stats: Dict[str, float]
    mu: float

StatisticalResult = Union[
    ANOVAResult,
    PairedTTestResultResponse,
    IndependentTTestResultResponse,
    OneSampleTTestResultResponse
] 