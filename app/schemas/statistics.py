from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union

class TestType(str, Enum):
    ONE_WAY_ANOVA = "OneWayANOVA"
    PAIRED_T_TEST = "PairedTTest"
    INDEPENDENT_T_TEST = "IndependentTTest"
    ONE_SAMPLE_T_TEST = "OneSampleTTest"

class HypothesisType(str, Enum):
    TWO_TAILED_SAME = "TwoTailedSame"
    TWO_TAILED_DIFF = "TwoTailedDiff"
    RIGHT_TAILED = "RightTailed"
    LEFT_TAILED = "LeftTailed"

class MissingValueHandling(str, Enum):
    PAIRWISE = "pairwise"
    LISTWISE_DELETION = "ListwiseDeletion"

class EffectSizeType(str, Enum):
    ETA_SQUARED = "Eta_Squared"
    COHENS_D = "Cohens_D"
    STANDARDIZED_MEAN_DIFFERENCE = "Standardized_Mean_Difference"
    NONE = ""

class StatisticRequest(BaseModel):
    test: TestType
    hypothesis: HypothesisType
    missingValueHandling: MissingValueHandling
    meanDifference: bool = False
    confidenceInterval: int = Field(ge=0, le=100)
    effectSize: EffectSizeType
    effectSizeValue: float
    descriptiveStats: bool
    value: Dict[str, List[Union[int, float]]]

class RenameStatisticRequest(BaseModel):
    new_alias: str

class StatisticalTestInfo(BaseModel):
    id: int
    alias: str

class StatisticalTestIdList(BaseModel):
    success: bool
    tests: List[StatisticalTestInfo]
    count: int

class StatisticalResultResponse(BaseModel):
    success: bool
    test_id: int
    alias: str
    test_method: str
    statistical_test_result: Dict
    results: Optional[str] = None
    conclusion: Optional[str] = None