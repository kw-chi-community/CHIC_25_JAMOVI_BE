from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from models import Project, get_db, ProjectPermission, TableData
from middleware.auth import get_current_user
from schemas import ProjectCreate, ProjectNameUpdate
from sqlalchemy.exc import SQLAlchemyError
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
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

router = APIRouter(prefix="/projects")

@router.post("/create")
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        if len(project.name) > 250:
            return {
                "success": False,
                "detail": "name is tooo long"
            }
            
        if len(project.description.encode('utf-8')) > 60000:
            return {
                "success": False,
                "detail": "description is tooo long"
            }

        existing_project = db.query(Project).filter(
            Project.name == project.name,
            Project.user_id == current_user["user"]
        ).first()
        
        if existing_project:
            raise HTTPException(
                status_code=400,
                detail="Project with this name already exists for this user"
            )
        
        new_project = Project(
            name=project.name,
            description=project.description,
            user_id=current_user["user"],
            visibility="private"
        )
        
        db.add(new_project)
        db.commit()
        db.refresh(new_project)
        
        return {
            "success": True,
            "detail": "Project created successfully",
            "project_id": new_project.id,
            "project_name": new_project.name,
            "project_description": new_project.description,
            "project_visibility": new_project.visibility,
            "project_user_id": new_project.user_id
        }
        
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error occurred while creating project"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Same name project already exists"
        )

@router.get("/", response_model=list)
def get_user_projects(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    인증된 사용자가 만든 모든 프로젝트를 ID 순서대로 가져오는 엔드포인트
    """
    projects = db.query(Project).filter(Project.user_id == current_user["user"]).order_by(Project.id.asc()).all()

    if not projects:
        return []

    return [
        {
            "id": project.id,
            "name": project.name,
            "visibility": project.visibility,
            "description": project.description,
            "user_id": project.user_id
        }
        for project in projects
    ]


@router.get("/{project_id}", response_model=dict)
def get_user_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    인증된 사용자의 특정 프로젝트를 가져오거나,
    visibility가 'etc'일 경우 ProjectPermission 테이블에서 권한 확인 및 반환.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    permissions = []

    if project.visibility == "etc":
        permissions = db.query(ProjectPermission).filter(
            ProjectPermission.project_id == project_id
        ).all()

    response = {
        "id": project.id,
        "user_id": project.user_id,
        "name": project.name,
        "visibility": project.visibility,
        "description": project.description,
    }

    if permissions:
        response["permissions"] = [
            {
                "user_id": permission.user_id,
                "is_editor": permission.is_editor,
            }
            for permission in permissions
        ]

    return response

@router.delete("/{project_id}", response_model=dict)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    현재 인증된 사용자가 소유한 프로젝트를 삭제하는 엔드포인트.
    """
    # 프로젝트가 존재하는지 확인합니다.
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 현재 사용자가 프로젝트의 소유자인지 확인합니다.
    if project.user_id != current_user["user"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this project")
    
    try:
        db.delete(project)
        db.commit()
        return {"success": True, "detail": "Project deleted successfully"}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error deleting project: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred while deleting project")

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
    # 수정 대상 프로젝트 조회
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 프로젝트 소유자 권한 확인
    if project.user_id != current_user["user"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this project")
    
    # 동일 사용자의 다른 프로젝트 중 동일 이름 존재 여부 확인
    existing_project = db.query(Project).filter(
        Project.name == update_data.name,
        Project.user_id == current_user["user"],
        Project.id != project_id
    ).first()
    if existing_project:
        raise HTTPException(
            status_code=400,
            detail="Project with this name already exists for this user"
        )
    
    # 프로젝트 이름 업데이트
    project.name = update_data.name
    try:
        db.commit()
        db.refresh(project)
        return {
            "success": True,
            "detail": "Project name updated successfully",
            "project_id": project.id,
            "project_name": project.name
        }
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error updating project name: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred while updating project")

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
            
        logger.info(f"current_user: {current_user}")
        
        project = db.query(Project).filter(Project.id == project_id).first()
        logger.info(f"project: {project}")

        if not project:
            logger.info(f"Project {project_id} not found")
            await websocket.close(code=4002)
            return
            
        permission = db.query(ProjectPermission).filter(
            ProjectPermission.project_id == project_id,
            ProjectPermission.user_id == current_user["user"]
        ).first()
        logger.info(f"permission: {permission}")
        
        if not permission and not (
            project.user_id == current_user["user"] or 
            project.visibility == "public_all_editor"
        ):
            logger.info("no permission")
            await websocket.close(code=4003)
            return
            
        initial_grid = [['' for _ in range(20)] for _ in range(10)]
        logger.info(f"grid initialized")

        table_data_list = db.query(TableData).filter(
            TableData.project_id == project_id
        ).all()
        logger.info(f"table_data_list: {table_data_list}")

        for data in table_data_list:
            if 0 <= data.row_num < 10 and 0 <= data.col_num < 20:
                initial_grid[data.row_num][data.col_num] = data.value
        
        initial_data = {
            "type": "initial_data",
            "success": True,
            "data": initial_grid
        }
        await websocket.send_json(initial_data)
        logger.info(f"initial_data sent")
        
        while True:
            try:
                data = await websocket.receive_json()
                logger.info(f"got data: [{data.get('row')}, {data.get('col')}] = {data.get('value')}")
                row_num = data.get("row")
                col_num = data.get("col")
                value = data.get("value")
                
                if not (0 <= row_num < 1000 and 0 <= col_num < 1000): # 테이블 크기가 무한하게 가는 건 막아야겠죠..?
                    await websocket.send_json({
                        "success": False,
                        "message": "Invalid row or column index"
                    })
                    continue
                
                table_data = db.query(TableData).filter(
                    TableData.project_id == project_id,
                    TableData.row_num == row_num,
                    TableData.col_num == col_num
                ).first()
                logger.info(f"table_data: {table_data}")

                if table_data:
                    table_data.value = value
                else:
                    table_data = TableData(
                        project_id=project_id,
                        row_num=row_num,
                        col_num=col_num,
                        value=value
                    )
                    db.add(table_data)
                    
                db.commit()
                logger.info(f"{project_id} | {row_num}, {col_num} = {value} table_data committed")
                
                update_message = {
                    "success": True,
                    "type": "update",
                    "row": row_num,
                    "col": col_num,
                    "value": value
                }
                await websocket.send_json(update_message)
                
            except WebSocketDisconnect:
                logger.info("websocket disconnected")
                return
            except Exception as e:
                logger.error(f"Error in websocket loop: {str(e)}")
                if not websocket.client_state.DISCONNECTED:
                    await websocket.close(code=4000)
                return
            
    except Exception as e:
        logger.error(f"websocket error: {str(e)}")
        if not websocket.client_state.DISCONNECTED:
            await websocket.close(code=4000)

            