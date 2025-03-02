from pydantic import BaseModel

class llmResultRequest(BaseModel):
    test_type: str
    question: str