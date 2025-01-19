from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import Project, get_db, ProjectPermission
from .auth import auth_middleware

router = APIRouter()

@router.get("/projects", response_model=list)
def get_user_projects(
    db: Session = Depends(get_db),
    current_user=Depends(auth_middleware)
):
    """
    인증된 사용자가 만든 모든 프로젝트를 ID 순서대로 가져오는 엔드포인트
    """
    projects = db.query(Project).filter(Project.user_id == current_user.id).order_by(Project.id.asc()).all()

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


@router.get("/projects/{project_id}", response_model=dict)
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