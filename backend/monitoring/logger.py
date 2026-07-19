"""
Logger - Enhanced logging system untuk workflow execution.
Menyediakan structured logging dengan multiple output.
"""

import os
import json
from datetime import datetime
from typing import Optional, Callable
from dataclasses import dataclass, field, asdict
from loguru import logger


@dataclass
class LogEntry:
    """Satu entry log."""
    timestamp: str = ""
    level: str = "INFO"
    message: str = ""
    execution_id: str = ""
    step_id: str = ""
    workflow_id: str = ""
    data: dict = field(default_factory=dict)


class ExecutionLogger:
    """
    Logger khusus untuk workflow execution.
    Menyediakan log terstruktur yang bisa dikirim ke UI.
    
    Contoh:
        exec_logger = ExecutionLogger("exec_001", "wf_001")
        exec_logger.info("Workflow started", {"total_steps": 5})
        exec_logger.error("Step failed", {"step_id": "step_1", "error": "..."})
    """
    
    def __init__(
        self,
        execution_id: str = "",
        workflow_id: str = "",
        logs_dir: str = "logs",
        callback: Optional[Callable] = None,
    ):
        self.execution_id = execution_id
        self.workflow_id = workflow_id
        self.logs_dir = logs_dir
        self.callback = callback
        self._entries: list[LogEntry] = []
        
        os.makedirs(logs_dir, exist_ok=True)
    
    def _log(self, level: str, message: str, step_id: str = "", data: dict = None) -> LogEntry:
        """Internal method untuk membuat log entry."""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level.upper(),
            message=message,
            execution_id=self.execution_id,
            step_id=step_id,
            workflow_id=self.workflow_id,
            data=data or {},
        )
        
        self._entries.append(entry)
        
        # Log ke loguru
        getattr(logger, level.lower(), logger.info)(f"[{self.execution_id}] {message}")
        
        # Callback ke UI
        if self.callback:
            self.callback(asdict(entry))
        
        # Simpan ke file JSON
        self._save_to_file(entry)
        
        return entry
    
    def _save_to_file(self, entry: LogEntry) -> None:
        """Simpan log entry ke file JSON."""
        if not self.execution_id:
            return
        
        log_file = os.path.join(
            self.logs_dir,
            f"exec_{self.execution_id}.jsonl"
        )
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"Failed to save log to file: {e}")
    
    def info(self, message: str, step_id: str = "", data: dict = None) -> LogEntry:
        return self._log("INFO", message, step_id, data)
    
    def success(self, message: str, step_id: str = "", data: dict = None) -> LogEntry:
        return self._log("SUCCESS", message, step_id, data)
    
    def warning(self, message: str, step_id: str = "", data: dict = None) -> LogEntry:
        return self._log("WARNING", message, step_id, data)
    
    def error(self, message: str, step_id: str = "", data: dict = None) -> LogEntry:
        return self._log("ERROR", message, step_id, data)
    
    def debug(self, message: str, step_id: str = "", data: dict = None) -> LogEntry:
        return self._log("DEBUG", message, step_id, data)
    
    def get_entries(self, level: Optional[str] = None) -> list[LogEntry]:
        """Dapatkan semua log entries, filter by level."""
        if level:
            return [e for e in self._entries if e.level == level.upper()]
        return list(self._entries)
    
    def get_recent(self, count: int = 10) -> list[LogEntry]:
        """Dapatkan N log entries terakhir."""
        return self._entries[-count:]
    
    def get_summary(self) -> dict:
        """Dapatkan summary log."""
        total = len(self._entries)
        by_level = {}
        for entry in self._entries:
            by_level[entry.level] = by_level.get(entry.level, 0) + 1
        
        return {
            "total": total,
            "by_level": by_level,
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
        }
    
    def export_json(self, file_path: str) -> None:
        """Export semua log ke file JSON."""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(
                [asdict(e) for e in self._entries],
                f,
                indent=2,
                ensure_ascii=False,
            )
    
    def clear(self) -> None:
        """Clear semua entries in memory."""
        self._entries.clear()