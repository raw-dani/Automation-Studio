"""
Workflow Parser - Membaca, memvalidasi, dan mengelola workflow dari file JSON.
"""

import json
import os
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime


class WorkflowValidationError(Exception):
    """Error saat validasi workflow."""
    pass


@dataclass
class WorkflowStep:
    """Representasi sebuah step dalam workflow."""
    id: str
    type: str
    label: str = ""
    params: dict = field(default_factory=dict)
    on_error: str = "stop"  # stop, skip, retry
    retry: dict = field(default_factory=lambda: {"max_retries": 3, "delay": 2000})
    children: list = field(default_factory=list)  # Untuk if_else, loop, parallel_group


@dataclass
class Workflow:
    """Representasi sebuah workflow lengkap."""
    id: str
    name: str
    version: str = "1.0"
    url: str = ""
    data_source: Optional[dict] = None
    steps: list[WorkflowStep] = field(default_factory=list)
    monitoring: dict = field(default_factory=lambda: {
        "screenshot_on_error": True,
        "screenshot_on_step": False,
        "log_level": "INFO"
    })
    created_at: str = ""
    updated_at: str = ""


class WorkflowParser:
    """
    Parser untuk membaca dan memvalidasi workflow dari file JSON.
    
    Contoh penggunaan:
        parser = WorkflowParser()
        workflow = parser.load("workflows/sample_workflow.json")
        print(workflow.name)
    """
    
    VALID_ACTIONS = {
        "click", "http_submit", "input_text", "input_date", "select", "select_dropdown", "select2", "radio_select",
        "wait", "upload_file", "loop", "if_else", "navigate", "parallel_group"
    }
    
    VALID_ON_ERROR = {"stop", "skip", "retry"}
    
    def load(self, file_path: str) -> Workflow:
        """
        Load workflow dari file JSON.
        
        Args:
            file_path: Path ke file workflow JSON.
            
        Returns:
            Workflow object.
            
        Raises:
            FileNotFoundError: Jika file tidak ditemukan.
            WorkflowValidationError: Jika format workflow tidak valid.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Workflow file tidak ditemukan: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return self.parse(data)
    
    def parse(self, data: dict) -> Workflow:
        """
        Parse dictionary menjadi Workflow object.
        
        Args:
            data: Dictionary dari JSON workflow.
            
        Returns:
            Workflow object.
            
        Raises:
            WorkflowValidationError: Jika format workflow tidak valid.
        """
        self._validate_workflow(data)
        
        steps = []
        for step_data in data.get("steps", []):
            step = self._parse_step(step_data)
            steps.append(step)
        
        now = datetime.now().isoformat()
        
        return Workflow(
            id=data["id"],
            name=data["name"],
            version=data.get("version", "1.0"),
            url=data.get("url", ""),
            data_source=data.get("data_source"),
            steps=steps,
            monitoring=data.get("monitoring", {
                "screenshot_on_error": True,
                "screenshot_on_step": False,
                "log_level": "INFO"
            }),
            created_at=data.get("created_at", now),
            updated_at=data.get("updated_at", now),
        )
    
    def _parse_step(self, data: dict) -> WorkflowStep:
        """Parse dictionary step menjadi WorkflowStep object."""
        self._validate_step(data)
        
        children = []
        if data["type"] == "if_else":
            for child_data in data.get("then", []) + data.get("else", []):
                children.append(self._parse_step(child_data))
        elif data["type"] in ("loop", "parallel_group"):
            for child_data in data.get("steps", []):
                children.append(self._parse_step(child_data))
        
        return WorkflowStep(
            id=data["id"],
            type=data["type"],
            label=data.get("label", ""),
            params=data.get("params", {}),
            on_error=data.get("on_error", "stop"),
            retry=data.get("retry", {"max_retries": 3, "delay": 2000}),
            children=children,
        )
    
    def _validate_workflow(self, data: dict) -> None:
        """Validasi struktur workflow."""
        if not isinstance(data, dict):
            raise WorkflowValidationError("Workflow harus berupa object JSON.")
        
        required_fields = ["id", "name", "steps"]
        for field in required_fields:
            if field not in data:
                raise WorkflowValidationError(f"Field '{field}' wajib ada di workflow.")
        
        if not isinstance(data["steps"], list):
            raise WorkflowValidationError("Field 'steps' harus berupa array.")
        
        if len(data["steps"]) == 0:
            raise WorkflowValidationError("Workflow harus memiliki minimal 1 step.")
    
    def _validate_step(self, data: dict) -> None:
        """Validasi struktur step."""
        if not isinstance(data, dict):
            raise WorkflowValidationError("Setiap step harus berupa object JSON.")
        
        if "id" not in data:
            raise WorkflowValidationError("Setiap step wajib memiliki field 'id'.")
        
        if "type" not in data:
            raise WorkflowValidationError(f"Step '{data.get('id', 'unknown')}' wajib memiliki field 'type'.")
        
        if data["type"] not in self.VALID_ACTIONS:
            raise WorkflowValidationError(
                f"Step '{data['id']}' memiliki type '{data['type']}' yang tidak valid. "
                f"Valid types: {', '.join(sorted(self.VALID_ACTIONS))}"
            )
        
        on_error = data.get("on_error", "stop")
        if on_error not in self.VALID_ON_ERROR:
            raise WorkflowValidationError(
                f"Step '{data['id']}' memiliki on_error '{on_error}' yang tidak valid. "
                f"Valid values: {', '.join(self.VALID_ON_ERROR)}"
            )
    
    def save(self, workflow: Workflow, file_path: str) -> None:
        """
        Simpan workflow ke file JSON.
        
        Args:
            workflow: Workflow object.
            file_path: Path untuk menyimpan file.
        """
        workflow.updated_at = datetime.now().isoformat()
        
        data = {
            "id": workflow.id,
            "name": workflow.name,
            "version": workflow.version,
            "url": workflow.url,
            "data_source": workflow.data_source,
            "steps": self._steps_to_dict(workflow.steps),
            "monitoring": workflow.monitoring,
            "created_at": workflow.created_at,
            "updated_at": workflow.updated_at,
        }
        
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _steps_to_dict(self, steps: list[WorkflowStep]) -> list[dict]:
        """Konversi list WorkflowStep ke list dictionary."""
        result = []
        for step in steps:
            step_dict = {
                "id": step.id,
                "type": step.type,
                "label": step.label,
                "params": dict(step.params),
                "on_error": step.on_error,
                "retry": dict(step.retry),
            }
            if step.children:
                step_dict["steps"] = self._steps_to_dict(step.children)
            result.append(step_dict)
        return result
    
    def list_workflows(self, workflows_dir: str = "workflows") -> list[dict]:
        """
        List semua workflow yang tersedia.
        
        Args:
            workflows_dir: Directory workflow files.
            
        Returns:
            List of dict: [{"id": "...", "name": "...", "file": "..."}, ...]
        """
        workflows = []
        if not os.path.exists(workflows_dir):
            return workflows
        
        for filename in os.listdir(workflows_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(workflows_dir, filename)
                try:
                    workflow = self.load(file_path)
                    workflows.append({
                        "id": workflow.id,
                        "name": workflow.name,
                        "version": workflow.version,
                        "file": filename,
                        "steps_count": len(workflow.steps),
                        "updated_at": workflow.updated_at,
                    })
                except Exception:
                    pass  # Skip file yang corrupt
        
        return workflows

