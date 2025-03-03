from pydantic import BaseModel
from typing import Optional

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectNameUpdate(BaseModel):
    name: str


class ProjectUpdate(BaseModel):
    name: str
    description: Optional[str] = None