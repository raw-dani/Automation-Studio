"""
Excel Data Source - Membaca data dari file Excel (.xlsx, .xls).
"""

import os
from typing import Iterator
from backend.data_sources.base_source import BaseDataSource, DataRow


class ExcelDataSource(BaseDataSource):
    """Membaca data dari file Excel menggunakan pandas + openpyxl."""
    
    @property
    def name(self) -> str:
        return "excel"
    
    def validate_config(self, config: dict) -> list[str]:
        errors = []
        file_path = config.get("file_path", "")
        if not file_path:
            errors.append("Parameter 'file_path' wajib diisi.")
        elif not os.path.exists(file_path):
            errors.append(f"File tidak ditemukan: {file_path}")
        elif not file_path.endswith((".xlsx", ".xls")):
            errors.append("File harus berekstensi .xlsx atau .xls")
        return errors
    
    def read(self, config: dict) -> Iterator[DataRow]:
        """
        Baca data dari Excel.
        
        Config:
            file_path: Path ke file Excel
            sheet: Nama sheet (default: Sheet1)
            header_row: Baris header (default: 0)
            start_row: Baris mulai baca data (default: 1, setelah header)
        """
        import pandas as pd
        
        file_path = config.get("file_path", "")
        sheet = config.get("sheet", "Sheet1")
        header_row = config.get("header_row", 0)
        
        if not os.path.exists(file_path):
            return
        
        # Baca Excel dengan fallback jika sheet tidak ditemukan
        try:
            df = pd.read_excel(
                file_path,
                sheet_name=sheet,
                header=header_row,
                dtype=str,
            )
        except ValueError:
            # Fallback: gunakan sheet pertama
            xls = pd.ExcelFile(file_path)
            if xls.sheet_names:
                df = pd.read_excel(
                    file_path,
                    sheet_name=xls.sheet_names[0],
                    header=header_row,
                    dtype=str,
                )
            else:
                raise
        
        # Hapus kolom yang semua NaN
        df = df.dropna(axis=1, how='all')
        
        # Isi NaN dengan string kosong
        df = df.fillna("")
        
        # Convert ke dict dan yield per baris
        for idx, row in df.iterrows():
            data = row.to_dict()
            # Convert semua value ke string
            data = {str(k): str(v) for k, v in data.items()}
            
            yield DataRow(
                data=data,
                row_number=idx + 2,  # +2 karena header di baris 1, data mulai baris 2
                source_name=file_path,
            )
    
    def get_sheet_names(self, file_path: str) -> list[str]:
        """Dapatkan daftar sheet names dari file Excel."""
        import pandas as pd
        
        if not os.path.exists(file_path):
            return []
        
        xls = pd.ExcelFile(file_path)
        return xls.sheet_names
    
    def get_preview(self, config: dict, max_rows: int = 5) -> list[dict]:
        """Preview data dari Excel."""
        rows = []
        for i, row in enumerate(self.read(config)):
            if i >= max_rows:
                break
            rows.append(row.data)
        return rows