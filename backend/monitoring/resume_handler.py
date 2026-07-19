"""
Resume Handler - Menyimpan state workflow untuk resume jika gagal.
Memungkinkan workflow dilanjutkan dari step terakhir yang gagal.
"""

import os
import json
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field, asdict
from loguru import logger


@dataclass
class Checkpoint:
    """Checkpoint state workflow."""
    execution_id: str
    workflow_id: str
    workflow_name: str
    last_completed_step: str = ""
    last_completed_index: int = -1
    total_steps: int = 0
    status: str = "running"  # running, paused, failed, completed
    variables: dict = field(default_factory=dict)
    current_data_index: int = 0  # Index data source saat ini
    started_at: str = ""
    updated_at: str = ""
    error_message: str = ""


class ResumeHandler:
    """
    Handler untuk menyimpan dan me-restore state workflow.
    
    Contoh:
        handler = ResumeHandler("checkpoints")
        handler.save_checkpoint(execution_id, {
            "last_completed_step": "step_3",
            "last_completed_index": 2,
            ...
        })
        checkpoint = handler.load_checkpoint(execution_id)
        # Resume dari step terakhir
    """
    
    def __init__(self, checkpoints_dir: str = "checkpoints"):
        self.checkpoints_dir = checkpoints_dir
        os.makedirs(checkpoints_dir, exist_ok=True)
    
    def _get_checkpoint_path(self, execution_id: str) -> str:
        """Dapatkan path file checkpoint."""
        return os.path.join(self.checkpoints_dir, f"{execution_id}.json")
    
    def save_checkpoint(self, execution_id: str, data: dict) -> bool:
        """
        Simpan checkpoint.
        
        Args:
            execution_id: ID eksekusi.
            data: Data state yang akan disimpan.
            
        Returns:
            True jika berhasil.
        """
        try:
            filepath = self._get_checkpoint_path(execution_id)
            
            checkpoint = {
                "execution_id": execution_id,
                "workflow_id": data.get("workflow_id", ""),
                "workflow_name": data.get("workflow_name", ""),
                "last_completed_step": data.get("last_completed_step", ""),
                "last_completed_index": data.get("last_completed_index", -1),
                "total_steps": data.get("total_steps", 0),
                "status": data.get("status", "running"),
                "variables": data.get("variables", {}),
                "current_data_index": data.get("current_data_index", 0),
                "started_at": data.get("started_at", datetime.now().isoformat()),
                "updated_at": datetime.now().isoformat(),
                "error_message": data.get("error_message", ""),
            }
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(checkpoint, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Checkpoint saved: {execution_id} (step: {checkpoint['last_completed_step']})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return False
    
    def load_checkpoint(self, execution_id: str) -> Optional[dict]:
        """
        Load checkpoint.
        
        Args:
            execution_id: ID eksekusi.
            
        Returns:
            Dict checkpoint atau None jika tidak ditemukan.
        """
        filepath = self._get_checkpoint_path(execution_id)
        
        if not os.path.exists(filepath):
            logger.warning(f"Checkpoint not found: {execution_id}")
            return None
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
            
            logger.info(f"Checkpoint loaded: {execution_id} (step: {checkpoint.get('last_completed_step', 'N/A')})")
            return checkpoint
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
    
    def delete_checkpoint(self, execution_id: str) -> bool:
        """Hapus checkpoint setelah sukses."""
        filepath = self._get_checkpoint_path(execution_id)
        
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Checkpoint deleted: {execution_id}")
            return True
        
        return False
    
    def list_checkpoints(self) -> list[dict]:
        """List semua checkpoint yang tersedia."""
        if not os.path.exists(self.checkpoints_dir):
            return []
        
        checkpoints = []
        for f in os.listdir(self.checkpoints_dir):
            if not f.endswith(".json"):
                continue
            
            filepath = os.path.join(self.checkpoints_dir, f)
            try:
                with open(filepath, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                checkpoints.append(data)
            except Exception:
                continue
        
        return sorted(checkpoints, key=lambda x: x.get("updated_at", ""), reverse=True)
    
    def has_checkpoint(self, execution_id: str) -> bool:
        """Cek apakah checkpoint exists."""
        return os.path.exists(self._get_checkpoint_path(execution_id))
    
    def cleanup_old(self, max_age_days: int = 7) -> int:
        """Hapus checkpoint lama."""
        if not os.path.exists(self.checkpoints_dir):
            return 0
        
        now = datetime.now().timestamp()
        max_age = max_age_days * 86400
        deleted = 0
        
        for f in os.listdir(self.checkpoints_dir):
            if not f.endswith(".json"):
                continue
            
            filepath = os.path.join(self.checkpoints_dir, f)
            file_age = now - os.stat(filepath).st_mtime
            
            if file_age > max_age:
                os.remove(filepath)
                deleted += 1
        
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old checkpoints")
        
        return deleted