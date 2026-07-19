"""
Base class untuk semua data source.
Setiap data source harus meng-extend class ini.
"""

from abc import ABC, abstractmethod
from typing import Iterator, Optional
from dataclasses import dataclass, field


@dataclass
class DataRow:
    """Satu baris data dari data source."""
    data: dict
    row_number: int
    source_name: str = ""


class BaseDataSource(ABC):
    """
    Abstract base class untuk semua data source.
    
    Contoh implementasi:
        class ExcelDataSource(BaseDataSource):
            @property
            def name(self) -> str:
                return "excel"
            
            def read(self, config: dict) -> Iterator[DataRow]:
                # baca Excel, yield DataRow per baris
                pass
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nama unik data source."""
        pass
    
    @abstractmethod
    def read(self, config: dict) -> Iterator[DataRow]:
        """
        Baca data dari source.
        
        Args:
            config: Konfigurasi data source (file path, sheet, query, dll).
            
        Yields:
            DataRow per baris data.
        """
        pass
    
    def validate_config(self, config: dict) -> list[str]:
        """
        Validasi konfigurasi data source.
        Returns list of error messages, kosong jika valid.
        """
        return []
    
    def get_preview(self, config: dict, max_rows: int = 5) -> list[dict]:
        """
        Preview data (untuk UI).
        
        Args:
            config: Konfigurasi data source.
            max_rows: Jumlah baris maksimal untuk preview.
            
        Returns:
            List of dict data.
        """
        rows = []
        for i, row in enumerate(self.read(config)):
            if i >= max_rows:
                break
            rows.append(row.data)
        return rows