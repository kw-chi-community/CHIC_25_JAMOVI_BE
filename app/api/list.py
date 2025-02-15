import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from models import (
    StatisticalTest,
    Project,
    User,
    get_db
)

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


router = APIRouter(prefix="/stats", tags=["Statistics"])

# 응답 모델
class StatisticalTestListItem(BaseModel):
    test_id: int
    test_method: str
    created_at: str
    project_name: str
    conclusion: Optional[str]
    image_url: Optional[str]
    hypothesis: str
    effect_size: Optional[str]

class StatisticalTestListResponse(BaseModel):
    total_count: int
    results: List[StatisticalTestListItem]

@router.get("/results", response_model=StatisticalTestListResponse)
async def list_statistical_results(
    request: Request,
    project_id: Optional[int] = Query(None, description="특정 프로젝트 필터링"),
    test_method: Optional[str] = Query(None, description="테스트 유형 필터링"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    try:
        # 인증된 사용자 정보 추출
        current_user = request.state.user
        if not current_user:
            raise HTTPException(status_code=401, detail="Unauthorized")

        # 기본 쿼리 구성
        query = db.query(StatisticalTest).join(Project).join(User).filter(
            User.id == current_user['id']
        )

        # 필터 조건 적용
        if project_id:
            query = query.filter(Project.id == project_id)
        if test_method:
            query = query.filter(StatisticalTest.test_method == test_method)

        # 전체 개수 조회
        total_count = query.count()

        # 페이징 처리
        results = query.order_by(StatisticalTest.id.desc()).offset(
            (page - 1) * limit
        ).limit(limit).all()

        logger.info(f"Retrieved {len(results)} statistical test results")

        # 응답 형식 변환
        return {
            "total_count": total_count,
            "results": [
                {
                    "test_id": test.id,
                    "test_method": test.test_method,
                    "created_at": test.project.created_at.strftime("%Y-%m-%d %H:%M"),
                    "project_name": test.project.name,
                    "conclusion": test.conclusion,
                    "image_url": test.image_url,
                    "hypothesis": test.hypothesis,
                    "effect_size": test.effect_size
                }
                for test in results
            ]
        }

    except Exception as e:
        logger.error(f"Error listing stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

