from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(255))
    visibility = Column(String(50))  # public_all_editor, public_all_viewer, private, etc
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    modified_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    user = relationship("User", back_populates="projects")
    permissions = relationship("ProjectPermission", back_populates="project")
    statistical_tests = relationship("StatisticalTest", back_populates="project")
    tables = relationship("TableData", back_populates="project")

class ProjectPermission(Base): # etc일 경우 해당 테이블에서 권한 관리
    __tablename__ = "project_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    is_editor = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="project_permissions")
    project = relationship("Project", back_populates="permissions")