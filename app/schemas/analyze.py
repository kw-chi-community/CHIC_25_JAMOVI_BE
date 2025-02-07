from pydantic import BaseModel

class ExperimentData(BaseModel):
    statistics_result: dict # 통계 결과(json)
    statistical_method: str # 통계검정 방법
    experiment_design: str # 실험 설계 방법
    subject_info: str # 피험자 정보