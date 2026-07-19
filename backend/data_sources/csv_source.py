"""
CSV Data Source - Membaca data dari file CSV.
"""

import os
from typing import Iterator
from backend.data_sources.base_source import BaseDataSource, DataRow


class CsvDataSource(BaseDataSource):
    """Membaca data dari file CSV menggunakan pandas."""
    
    @property
    def name(self) -> str:
        return "csv"
    
    def validate_config(self, config: dict) -> list[str]:
        errors = []
        file_path = config.get("file_path", "")
        if not file_path:
            errors.append("Parameter 'file_path' wajib diisi.")
        elif not os.path.exists(file_path):
            errors.append(f"File tidak ditemukan: {file_path}")
        elif not file_path.endswith(".csv"):
            errors.append("File harus berekstensi .csv")
        return errors
    
    def read(self, config: dict) -> Iterator[DataRow]:
        """
        Baca data dari CSV.
        
        Config:
            file_path: Path ke file CSV
            delimiter: Pemisah (default: ,)
            encoding: Encoding file (default: utf-8)
            header_row: Baris header (default: 0)
        """
        import pandas as pd
        
        file_path = config.get("file_path", "")
        delimiter = config.get("delimiter", ",")
        encoding = config.get("encoding", "utf-8")
        header_row = config.get("header_row", 0)
        
        if not os.path.exists(file_path):
            return
        
        try:
            df = pd.read_csv(
                file_path,
                delimiter=delimiter,
                encoding=encoding,
                header=header_row,
                dtype=str,
            )
        except UnicodeDecodeError:
            # Fallback ke latin1 jika utf-8 gagal
            df = pd.read_csv(
                file_path,
                delimiter=delimiter,
                encoding="latin1",
                header=header_row,
                dtype=str,
            )
        
        # Hapus kolom yang semua NaN
        df = df.dropna(axis=1, how='all')
        
        # Isi NaN dengan string kosong
        df = df.fillna("")
        
        for idx, row in df.iterrows():
            data = row.to_dict()
            data = {str(k): str(v) for k, v in data.items()}
            
            yield DataRow(
                data=data,
                row_number=idx + 2,
                source_name=file_path,
            )
    
    def get_preview(self, config: dict, max_rows: int = 5) -> list[dict]:
        rows = []
        for i, row in enumerate(self.read(config)):
            if i >= max_rows:
                break
            rows.append(row.data)
        return rows