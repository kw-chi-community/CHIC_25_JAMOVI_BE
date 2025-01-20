from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from models import Project, get_db, ProjectPermission
from middleware.auth import get_current_user
from schemas import ProjectCreate
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(prefix="/projects")

@router.post("/create")
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
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