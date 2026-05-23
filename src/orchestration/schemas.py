from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class TaskResult(BaseModel):
    task_id: str
    task_name: str
    target: str
    status: str
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    depth: int = 0

class OrchestrationEvent(BaseModel):
    event_type: str
    target: str
    context: Dict[str, Any] = Field(default_factory=dict)
    depth: int = 0
