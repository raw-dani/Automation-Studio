"""
Pydantic models untuk FastAPI request/response schemas.
"""

from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class WorkflowStepSchema(BaseModel):
    """Schema untuk satu step dalam workflow."""
    id: str
    type: str
    label: str = ""
    params: dict = Field(default_factory=dict)
    on_error: str = "stop"
    retry: dict = Field(default_factory=lambda: {"max_retries": 3, "delay": 2000})


class WorkflowSchema(BaseModel):
    """Schema untuk workflow."""
    id: str
    name: str
    version: str = "1.0"
    url: str = ""
    data_source: Optional[dict] = None
    steps: list[WorkflowStepSchema] = Field(default_factory=list)
    monitoring: dict = Field(default_factory=lambda: {
        "screenshot_on_error": True,
        "screenshot_on_step": False,
        "log_level": "INFO"
    })


class WorkflowRunRequest(BaseModel):
    """Request untuk menjalankan workflow."""
    workflow_id: str
    workflow: Optional[WorkflowSchema] = None
    file_path: Optional[str] = None
    resume_from: Optional[str] = None
    start_url: Optional[str] = None


class WorkflowRunResponse(BaseModel):
    """Response dari eksekusi workflow."""
    execution_id: str
    workflow_id: str
    workflow_name: str
    status: str
    start_time: str
    end_time: str = ""
    duration_seconds: float = 0
    total_steps: int = 0
    success_count: int = 0
    failed_count: int = 0
    results: list[dict] = Field(default_factory=list)


class LogEntrySchema(BaseModel):
    """Schema untuk log entry."""
    timestamp: str
    level: str
    message: str
    execution_id: str = ""
    step_id: str = ""
    workflow_id: str = ""
    data: dict = Field(default_factory=dict)


class ScreenshotSchema(BaseModel):
    """Schema untuk screenshot."""
    filename: str
    path: str
    size: int
    created: str


class WorkflowListSchema(BaseModel):
    """Schema untuk daftar workflow."""
    id: str
    name: str
    version: str
    file: str
    steps_count: int
    updated_at: str


class HealthResponse(BaseModel):
    """Schema untuk health check."""
    status: str = "ok"
    app_name: str = "Automation Studio"
    version: str = "1.0.0"
    timestamp: str = ""