from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from models import Project, get_db, ProjectPermission, TableData
from middleware.auth import get_current_user
from schemas import ProjectCreate, ProjectNameUpdate
from sqlalchemy.exc import SQLAlchemyError
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
import logging
from datetime import datetime
from services import ProjectService

logger = logging.getLogger(__name__)

formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.setLevel(logging.INFO)

router = APIRouter()

@router.post("/create")
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return ProjectService.create_project(db, project, current_user)

@router.get("/", response_model=list)
def get_user_projects(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    인증된 사용자가 만든 모든 프로젝트를 ID 순서대로 가져오는 엔드포인트
    """
    return ProjectService.get_user_projects(db, current_user)

@router.get("/{project_id}", response_model=dict)
def get_user_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    인증된 사용자의 특정 프로젝트를 가져오거나,
    visibility가 'etc'일 경우 ProjectPermission 테이블에서 권한 확인 및 반환.
    """
    return ProjectService.get_user_project(db, project_id)

@router.delete("/{project_id}", response_model=dict)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    현재 인증된 사용자가 소유한 프로젝트를 삭제하는 엔드포인트.
    """
    return ProjectService.delete_project(db, project_id, current_user)

@router.put("/update/{project_id}", response_model=dict)
def update_project_name(
    project_id: int,
    update_data: ProjectNameUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    현재 인증된 사용자가 소유한 프로젝트의 이름을 변경하는 엔드포인트.
    프로젝트 이름 중복 여부도 체크하여 업데이트합니다.
    """
    return ProjectService.update_project_name(db, project_id, update_data, current_user)

@router.websocket("/table")
async def save_project_table(
    websocket: WebSocket,
    project_id: int,
    db: Session = Depends(get_db),
):
    try:
        await websocket.accept()
        logger.info("websocket accepted")
        
        current_user = await get_current_user(websocket=websocket)
        if not current_user:
            logger.info("Authentication failed")
            await websocket.close(code=4001)
            return

        success, error_code = await ProjectService.handle_table_websocket(
            websocket=websocket,
            project_id=project_id,
            db=db,
            current_user=current_user
        )

        if not success and error_code:
            await websocket.close(code=error_code)
            
    except Exception as e:
        logger.error(f"websocket error: {str(e)}")
        if not websocket.client_state.DISCONNECTED:
            await websocket.close(code=4000)