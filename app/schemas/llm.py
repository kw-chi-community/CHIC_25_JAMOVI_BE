from pydantic import BaseModel

class llmResultRequest(BaseModel):
    test_type: str
    question: str # statistical 결과
    statistical_test_id: int

class llmConclusionRequest(BaseModel):
    test_type: str
    experimental_design: str # 실험 설계 방식
    subject_info: str # 피험자 정보
    question: str # llm 결과 그대로 넣기?
    statistical_test_id: int