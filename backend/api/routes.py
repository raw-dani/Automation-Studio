"""
FastAPI Routes - REST API endpoints untuk Automation Studio.
Memungkinkan integrasi dengan sistem lain via HTTP.
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.api.schemas import (
    WorkflowRunRequest, WorkflowRunResponse, WorkflowSchema,
    LogEntrySchema, ScreenshotSchema, WorkflowListSchema, HealthResponse,
)
from backend.core.engine import ExecutionEngine
from backend.core.action_registry import ActionRegistry
from backend.core.workflow_parser import WorkflowParser, WorkflowValidationError
from backend.monitoring.logger import ExecutionLogger
from backend.monitoring.screenshot import ScreenshotManager
from backend.monitoring.resume_handler import ResumeHandler

from backend.actions.click_action import ClickAction
from backend.actions.input_text_action import InputTextAction
from backend.actions.wait_action import WaitAction
from backend.actions.select_dropdown_action import SelectDropdownAction
from backend.actions.upload_file_action import UploadFileAction
from backend.actions.loop_action import LoopAction
from backend.actions.if_else_action import IfElseAction
from backend.actions.navigate_action import NavigateAction
from backend.actions.select_action import SelectAction
from backend.actions.select2_action import Select2Action


def create_app(config: dict = None) -> FastAPI:
    """Buat FastAPI app dengan semua dependencies."""
    config = config or {}
    
    # Setup registries
    action_registry = ActionRegistry()
    action_registry.register(ClickAction())
    action_registry.register(InputTextAction())
    action_registry.register(WaitAction())
    action_registry.register(SelectDropdownAction())
    action_registry.register(SelectAction())
    action_registry.register(Select2Action())
    action_registry.register(UploadFileAction())
    action_registry.register(LoopAction())
    action_registry.register(IfElseAction())
    action_registry.register(NavigateAction())
    
    engine = ExecutionEngine(action_registry, config)
    parser = WorkflowParser()
    screenshot_mgr = ScreenshotManager(
        config.get("paths", {}).get("screenshots", "screenshots")
    )
    resume_handler = ResumeHandler("checkpoints")
    
    # Create FastAPI
    app = FastAPI(
        title="Automation Studio API",
        description="REST API untuk menjalankan dan memonitor workflow automasi",
        version="1.0.0",
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Store in app state
    app.state.engine = engine
    app.state.parser = parser
    app.state.screenshot_mgr = screenshot_mgr
    app.state.resume_handler = resume_handler
    app.state.config = config
    app.state.active_executions: dict[str, asyncio.Task] = {}
    
    return app


# Create default app
app = create_app()


@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        timestamp=datetime.now().isoformat(),
    )


@app.get("/api/health", response_model=HealthResponse)
async def api_health():
    """API health check."""
    return HealthResponse(
        timestamp=datetime.now().isoformat(),
    )


@app.get("/api/workflows", response_model=list[WorkflowListSchema])
async def list_workflows():
    """List semua workflow yang tersedia."""
    parser = app.state.parser
    workflows_dir = app.state.config.get("paths", {}).get("workflows", "workflows")
    return parser.list_workflows(workflows_dir)


@app.get("/api/workflows/{workflow_id}", response_model=WorkflowSchema)
async def get_workflow(workflow_id: str):
    """Dapatkan detail workflow."""
    parser = app.state.parser
    workflows_dir = app.state.config.get("paths", {}).get("workflows", "workflows")
    
    for wf in parser.list_workflows(workflows_dir):
        if wf["id"] == workflow_id:
            file_path = os.path.join(workflows_dir, wf["file"])
            workflow = parser.load(file_path)
            return WorkflowSchema(
                id=workflow.id,
                name=workflow.name,
                version=workflow.version,
                url=workflow.url,
                data_source=workflow.data_source,
                steps=[s.__dict__ for s in workflow.steps],
                monitoring=workflow.monitoring,
            )
    
    raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")


@app.post("/api/workflows/run", response_model=WorkflowRunResponse)
async def run_workflow(request: WorkflowRunRequest):
    """Jalankan workflow."""
    engine = app.state.engine
    parser = app.state.parser
    
    try:
        # Load workflow
        if request.file_path:
            workflow = parser.load(request.file_path)
        elif request.workflow:
            workflow_data = request.workflow.model_dump()
            workflow = parser.parse(workflow_data)
        else:
            raise HTTPException(status_code=400, detail="workflow or file_path required")
        
        # Run
        result = await engine.run(
            workflow=workflow,
            resume_from=request.resume_from,
            start_url=request.start_url,
        )
        
        return WorkflowRunResponse(**result)
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WorkflowValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/workflows/{workflow_id}/stop")
async def stop_workflow(workflow_id: str):
    """Hentikan eksekusi workflow."""
    engine = app.state.engine
    engine.stop()
    return {"status": "stopped", "workflow_id": workflow_id}


@app.get("/api/executions/{execution_id}/logs", response_model=list[LogEntrySchema])
async def get_execution_logs(execution_id: str):
    """Dapatkan log dari execution."""
    log_file = os.path.join("logs", f"exec_{execution_id}.jsonl")
    
    if not os.path.exists(log_file):
        raise HTTPException(status_code=404, detail="Logs not found")
    
    logs = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                logs.append(json.loads(line))
    
    return logs


@app.get("/api/executions/{execution_id}/screenshots", response_model=list[ScreenshotSchema])
async def get_execution_screenshots(execution_id: str):
    """Dapatkan screenshot dari execution."""
    screenshots = app.state.screenshot_mgr.list_screenshots(execution_id)
    
    result = []
    for s in screenshots:
        result.append(ScreenshotSchema(
            filename=s["filename"],
            path=s["path"],
            size=s["size"],
            created=s["created"],
        ))
    
    return result


@app.get("/api/screenshots/{filename}")
async def get_screenshot(filename: str):
    """Download screenshot file."""
    screenshots_dir = app.state.config.get("paths", {}).get("screenshots", "screenshots")
    filepath = os.path.join(screenshots_dir, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Screenshot not found")
    
    return FileResponse(filepath, media_type="image/png")


@app.get("/api/actions")
async def list_actions():
    """List semua action yang tersedia."""
    registry = ActionRegistry()
    registry.register(ClickAction())
    registry.register(InputTextAction())
    registry.register(WaitAction())
    registry.register(SelectDropdownAction())
    registry.register(SelectAction())
    registry.register(Select2Action())
    registry.register(UploadFileAction())
    registry.register(LoopAction())
    registry.register(IfElseAction())
    registry.register(NavigateAction())
    
    return registry.get_action_descriptions()


@app.get("/api/engine/status")
async def get_engine_status():
    """Dapatkan status engine saat ini."""
    engine = app.state.engine
    return {
        "is_running": engine.is_running,
        "is_paused": engine.is_paused,
        "current_step": engine.current_step.id if engine.current_step else None,
    }


def run_api(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Jalankan API server."""
    import uvicorn
    uvicorn.run("backend.api.routes:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    run_api()