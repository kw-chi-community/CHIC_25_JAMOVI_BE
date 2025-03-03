from fastapi import HTTPException, WebSocket
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models import Project, ProjectPermission, TableData
from schemas import ProjectCreate, ProjectUpdate
import logging
from datetime import datetime
from fastapi import WebSocketDisconnect

logger = logging.getLogger(__name__)

formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.setLevel(logging.INFO)

class ProjectService:
    @staticmethod
    def create_project(db: Session, project: ProjectCreate, current_user: dict):
        if len(project.name) > 250:
            return {"success": False, "detail": "name is too long"}
            
        if len(project.description.encode('utf-8')) > 60000:
            return {"success": False, "detail": "description is too long"}

        try:
            existing_project = db.query(Project).filter(
                Project.name == project.name,
                Project.user_id == current_user["user"]
            ).first()
            
            if existing_project:
                raise HTTPException(status_code=400, detail="Project with this name already exists for this user")
            
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
            raise HTTPException(status_code=500, detail="Database error occurred while creating project")
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Same name project already exists")

    @staticmethod
    def get_user_projects(db: Session, current_user: dict):
        projects = db.query(Project).filter(
            Project.user_id == current_user["user"]
        ).order_by(Project.id.asc()).all()

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

    @staticmethod
    def get_user_project(db: Session, project_id: int):
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
            "created_at": project.created_at,
            "modified_at": project.modified_at,
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

    @staticmethod
    def delete_project(db: Session, project_id: int, current_user: dict):
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
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

    @staticmethod
    def update_project(db: Session, project_id: int, update_data: ProjectUpdate, current_user: dict):
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if project.user_id != current_user["user"]:
            raise HTTPException(status_code=403, detail="Not authorized to update this project")
        
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
        
        project.name = update_data.name
        if update_data.description is not None:
            project.description = update_data.description
        
        try:
            db.commit()
            db.refresh(project)
            return {
                "success": True,
                "detail": "Project updated successfully",
                "project_id": project.id,
                "project_name": project.name,
                "project_description": project.description
            }
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating project name: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error occurred while updating project")

    @staticmethod
    async def handle_table_websocket(websocket: WebSocket, project_id: int, db: Session, current_user: dict):
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            logger.info(f"project: {project}")

            if not project:
                logger.info(f"Project {project_id} not found")
                return False, 4002

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
                return False, 4003

            initial_grid = [['' for _ in range(20)] for _ in range(100)]
            table_data_list = db.query(TableData).filter(
                TableData.project_id == project_id
            ).all()

            for data in table_data_list:
                if 0 <= data.row_num < 100 and 0 <= data.col_num < 20:
                    initial_grid[data.row_num][data.col_num] = data.value
            
            await websocket.send_json({
                "type": "initial_data",
                "success": True,
                "data": initial_grid
            })
            
            while True:
                data = await websocket.receive_json()
                row_num = data.get("row")
                col_num = data.get("col")
                value = data.get("value")
                
                if not (0 <= row_num < 100 and 0 <= col_num < 20):
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
                
                project.modified_at = datetime.now()
                db.commit()
                
                await websocket.send_json({
                    "success": True,
                    "type": "update",
                    "row": row_num,
                    "col": col_num,
                    "value": value
                })
                
        except WebSocketDisconnect:
            logger.info("websocket disconnected")
            return True, None
        except Exception as e:
            logger.error(f"Error in websocket handler: {str(e)}")
            return False, 4000