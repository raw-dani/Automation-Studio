"""
API Data Source - Mengambil data dari REST API endpoints.
"""

from typing import Iterator, Optional
from loguru import logger

from backend.data_sources.base_source import BaseDataSource, DataRow


class ApiDataSource(BaseDataSource):
    """
    Mengambil data dari REST API.
    
    Config:
        url: Endpoint URL
        method: HTTP method (GET, POST)
        headers: HTTP headers (dict)
        params: Query parameters (dict)
        body: Request body (dict, untuk POST)
        data_path: JSON path ke array data (misal: "data.items" atau "results")
        pagination: Konfigurasi pagination
    """
    
    @property
    def name(self) -> str:
        return "api"
    
    def validate_config(self, config: dict) -> list[str]:
        errors = []
        if not config.get("url"):
            errors.append("Parameter 'url' wajib diisi.")
        return errors
    
    def read(self, config: dict) -> Iterator[DataRow]:
        """
        Ambil data dari API.
        
        Config:
            url: Endpoint URL
            method: GET atau POST (default: GET)
            headers: Dict of HTTP headers
            params: Dict of query params
            body: Dict of JSON body (untuk POST)
            data_path: Path ke array data (contoh: "results" atau "data.items")
        """
        import httpx
        
        url = config.get("url", "")
        method = config.get("method", "GET").upper()
        headers = config.get("headers", {})
        params = config.get("params", {})
        body = config.get("body", None)
        data_path = config.get("data_path", "")
        
        if not url:
            return
        
        try:
            with httpx.Client(timeout=30.0) as client:
                if method == "GET":
                    response = client.get(url, headers=headers, params=params)
                elif method == "POST":
                    response = client.post(url, headers=headers, json=body, params=params)
                else:
                    response = client.get(url, headers=headers, params=params)
                
                response.raise_for_status()
                data = response.json()
                
                # Extract data from path
                if data_path:
                    items = self._get_nested_value(data, data_path)
                else:
                    items = data
                
                # Handle different response formats
                if isinstance(items, dict):
                    items = [items]
                elif not isinstance(items, list):
                    items = [{"data": str(items)}]
                
                for idx, item in enumerate(items):
                    if isinstance(item, dict):
                        row_data = {str(k): str(v) if v is not None else "" for k, v in item.items()}
                    else:
                        row_data = {"value": str(item)}
                    
                    yield DataRow(
                        data=row_data,
                        row_number=idx + 1,
                        source_name=url,
                    )
                    
        except Exception as e:
            logger.error(f"API request failed: {e}")
            raise
    
    def _get_nested_value(self, data: dict, path: str):
        """Ambil value dari nested dict menggunakan dot notation."""
        keys = path.split(".")
        current = data
        
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key, {})
            elif isinstance(current, list):
                # Jika list, coba akses index
                try:
                    idx = int(key)
                    current = current[idx] if idx < len(current) else {}
                except ValueError:
                    # Jika bukan index, ambil dari setiap item
                    result = []
                    for item in current:
                        if isinstance(item, dict):
                            result.append(item.get(key, {}))
                    current = result
            else:
                return current
        
        return current