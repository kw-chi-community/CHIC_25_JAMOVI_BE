from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class TableData(Base):
    __tablename__ = "table_data"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    row_num = Column(Integer)
    col_num = Column(Integer)
    value = Column(String(255))
    
    project = relationship("Project", back_populates="tables")
