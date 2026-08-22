"""
Base class for all workflow actions.
Setiap action harus meng-extend class ini dan mengimplementasikan method execute().
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class ActionStatus(Enum):
    """Status hasil eksekusi action."""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


@dataclass
class ActionResult:
    """Hasil eksekusi dari sebuah action."""
    status: ActionStatus
    message: str = ""
    data: Optional[dict] = None
    screenshot_path: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ExecutionContext:
    """
    Context yang dibagikan ke semua action selama eksekusi workflow.
    Berisi page browser, data source, dan state lainnya.
    """
    page: Any = None  # Playwright page object
    browser: Any = None  # Playwright browser object
    current_data: dict = field(default_factory=dict)  # Data row saat ini dari data source
    row_number: int = 0  # Nomor baris saat ini (1-based, 0 berarti bukan dari data source)
    workflow_id: str = ""
    execution_id: str = ""
    variables: dict = field(default_factory=dict)  # Variable yang bisa di-set selama eksekusi
    screenshots_dir: str = "screenshots"
    logs_dir: str = "logs"
    config: dict = field(default_factory=dict)
    is_running: bool = True
    is_paused: bool = False


class BaseAction(ABC):
    """
    Abstract base class untuk semua action.
    
    Contoh implementasi:
        class ClickAction(BaseAction):
            @property
            def name(self) -> str:
                return "click"
            
            async def execute(self, context: ExecutionContext, params: dict) -> ActionResult:
                # implementasi
                pass
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nama unik action (digunakan di workflow JSON sebagai 'type')."""
        pass
    
    @property
    def description(self) -> str:
        """Deskripsi action untuk ditampilkan di UI."""
        return self.__class__.__doc__ or ""
    
    @property
    def default_params(self) -> dict:
        """Default parameter untuk action ini."""
        return {}
    
    @abstractmethod
    async def execute(self, context: ExecutionContext, params: dict) -> ActionResult:
        """
        Execute action.
        
        Args:
            context: Execution context berisi page browser dan data.
            params: Parameter spesifik untuk action ini.
            
        Returns:
            ActionResult dengan status dan data.
        """
        pass
    
    def validate_params(self, params: dict) -> list[str]:
        """
        Validasi parameter action.
        Mengembalikan list error message, kosong jika valid.
        """
        return []