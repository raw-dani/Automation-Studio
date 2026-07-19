"""
Progress Tracker - Melacak progress eksekusi workflow step-by-step.
"""

from datetime import datetime
from typing import Optional, Callable
from dataclasses import dataclass, field, asdict


@dataclass
class StepProgress:
    """Progress satu step."""
    step_id: str
    step_type: str
    step_label: str = ""
    status: str = "pending"  # pending, running, retrying, success, failed, skipped
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: float = 0
    message: str = ""
    error: Optional[str] = None
    retry_count: int = 0
    screenshot_path: Optional[str] = None


@dataclass
class ExecutionProgress:
    """Progress keseluruhan workflow."""
    execution_id: str = ""
    workflow_id: str = ""
    workflow_name: str = ""
    status: str = "pending"  # pending, running, paused, completed, failed
    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    skipped_steps: int = 0
    percentage: float = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: float = 0
    current_step_id: str = ""
    steps: list = field(default_factory=list)


class ProgressTracker:
    """
    Melacak progress eksekusi workflow.
    Bisa di-subscribe oleh UI untuk real-time updates.
    
    Contoh:
        tracker = ProgressTracker()
        tracker.on_progress = lambda p: print(p)
        tracker.start("exec_001", "wf_001", "My Workflow", 5)
        tracker.start_step("step_1", "click", "Klik tombol")
        tracker.complete_step("step_1", "success")
    """
    
    def __init__(self):
        self._progress: Optional[ExecutionProgress] = None
        self.on_progress: Optional[Callable] = None
    
    def start(
        self,
        execution_id: str,
        workflow_id: str,
        workflow_name: str,
        total_steps: int,
    ) -> ExecutionProgress:
        """Mulai tracking progress."""
        self._progress = ExecutionProgress(
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            status="running",
            total_steps=total_steps,
            started_at=datetime.now().isoformat(),
        )
        self._notify()
        return self._progress
    
    def start_step(self, step_id: str, step_type: str, step_label: str = "") -> StepProgress:
        """Mulai tracking satu step."""
        if not self._progress:
            return StepProgress(step_id=step_id, step_type=step_type)
        
        step = StepProgress(
            step_id=step_id,
            step_type=step_type,
            step_label=step_label,
            status="running",
            started_at=datetime.now().isoformat(),
        )
        
        self._progress.current_step_id = step_id
        self._progress.steps.append(step)
        self._notify()
        return step
    
    def update_step(
        self,
        step_id: str,
        status: str,
        message: str = "",
        error: Optional[str] = None,
        retry_count: int = 0,
        screenshot_path: Optional[str] = None,
    ) -> None:
        """Update status satu step."""
        if not self._progress:
            return
        
        for step in self._progress.steps:
            if step.step_id == step_id:
                step.status = status
                step.message = message
                step.completed_at = datetime.now().isoformat()
                
                if step.started_at:
                    start = datetime.fromisoformat(step.started_at)
                    end = datetime.fromisoformat(step.completed_at)
                    step.duration_ms = (end - start).total_seconds() * 1000
                
                if error:
                    step.error = error
                if retry_count:
                    step.retry_count = retry_count
                if screenshot_path:
                    step.screenshot_path = screenshot_path
                
                # Update overall progress
                if status == "success":
                    self._progress.completed_steps += 1
                elif status == "failed":
                    self._progress.failed_steps += 1
                elif status == "skipped":
                    self._progress.skipped_steps += 1
                
                self._update_percentage()
                self._notify()
                break
    
    def complete(self, status: str = "completed") -> ExecutionProgress:
        """Selesaikan tracking."""
        if not self._progress:
            return ExecutionProgress()
        
        self._progress.status = status
        self._progress.completed_at = datetime.now().isoformat()
        
        if self._progress.started_at:
            start = datetime.fromisoformat(self._progress.started_at)
            end = datetime.fromisoformat(self._progress.completed_at)
            self._progress.duration_ms = (end - start).total_seconds() * 1000
        
        self._update_percentage()
        self._notify()
        return self._progress
    
    def pause(self) -> None:
        """Pause tracking."""
        if self._progress:
            self._progress.status = "paused"
            self._notify()
    
    def resume(self) -> None:
        """Resume tracking."""
        if self._progress:
            self._progress.status = "running"
            self._notify()
    
    def _update_percentage(self) -> None:
        """Update persentase progress."""
        if not self._progress or self._progress.total_steps == 0:
            return
        
        done = self._progress.completed_steps + self._progress.failed_steps + self._progress.skipped_steps
        self._progress.percentage = (done / self._progress.total_steps) * 100
    
    def _notify(self) -> None:
        """Notify callback."""
        if self.on_progress and self._progress:
            self.on_progress(asdict(self._progress))
    
    def get_progress(self) -> Optional[ExecutionProgress]:
        """Dapatkan progress saat ini."""
        return self._progress
    
    def get_summary(self) -> dict:
        """Dapatkan summary progress."""
        if not self._progress:
            return {}
        
        return {
            "execution_id": self._progress.execution_id,
            "workflow_name": self._progress.workflow_name,
            "status": self._progress.status,
            "total_steps": self._progress.total_steps,
            "completed": self._progress.completed_steps,
            "failed": self._progress.failed_steps,
            "skipped": self._progress.skipped_steps,
            "percentage": round(self._progress.percentage, 1),
            "duration_ms": round(self._progress.duration_ms, 0),
        }