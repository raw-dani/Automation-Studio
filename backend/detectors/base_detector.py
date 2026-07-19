"""
Base class untuk semua detector (OCR, Image Detection, dll).
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass, field


@dataclass
class DetectionResult:
    """Hasil deteksi."""
    success: bool
    data: Any = None
    confidence: float = 0.0
    message: str = ""
    error: Optional[str] = None


class BaseDetector(ABC):
    """
    Abstract base class untuk semua detector.
    
    Contoh:
        class OCRDetector(BaseDetector):
            @property
            def name(self) -> str:
                return "ocr"
            
            def detect(self, image_path: str, **kwargs) -> DetectionResult:
                # implementasi OCR
                pass
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nama unik detector."""
        pass
    
    @abstractmethod
    def detect(self, image_path: str, **kwargs) -> DetectionResult:
        """
        Lakukan deteksi pada gambar.
        
        Args:
            image_path: Path ke file gambar.
            **kwargs: Parameter tambahan spesifik detector.
            
        Returns:
            DetectionResult.
        """
        pass