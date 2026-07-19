"""
Database Data Source - Membaca data dari database menggunakan SQLAlchemy.
Mendukung MySQL, PostgreSQL, SQLite.
"""

from typing import Iterator, Optional
from loguru import logger

from backend.data_sources.base_source import BaseDataSource, DataRow


class DatabaseDataSource(BaseDataSource):
    """
    Membaca data dari database menggunakan SQLAlchemy.
    
    Config:
        dialect: mysql, postgresql, sqlite
        host: Host database
        port: Port database
        database: Nama database
        username: Username
        password: Password
        query: SQL query untuk mengambil data
    """
    
    @property
    def name(self) -> str:
        return "database"
    
    def validate_config(self, config: dict) -> list[str]:
        errors = []
        if not config.get("query"):
            errors.append("Parameter 'query' (SQL query) wajib diisi.")
        if not config.get("dialect"):
            errors.append("Parameter 'dialect' (mysql/postgresql/sqlite) wajib diisi.")
        return errors
    
    def _build_connection_string(self, config: dict) -> str:
        """Build SQLAlchemy connection string."""
        dialect = config.get("dialect", "sqlite")
        
        if dialect == "sqlite":
            db = config.get("database", "automation.db")
            return f"sqlite:///{db}"
        
        host = config.get("host", "localhost")
        port = config.get("port", "3306" if dialect == "mysql" else "5432")
        db = config.get("database", "")
        user = config.get("username", "")
        password = config.get("password", "")
        
        if dialect == "mysql":
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"
        elif dialect == "postgresql":
            return f"postgresql://{user}:{password}@{host}:{port}/{db}"
        
        return f"sqlite:///automation.db"
    
    def read(self, config: dict) -> Iterator[DataRow]:
        """
        Baca data dari database.
        
        Config:
            dialect: mysql, postgresql, sqlite
            host, port, database, username, password
            query: SQL query
        """
        from sqlalchemy import create_engine, text
        
        query = config.get("query", "")
        if not query:
            return
        
        try:
            conn_string = self._build_connection_string(config)
            engine = create_engine(conn_string)
            
            with engine.connect() as conn:
                result = conn.execute(text(query))
                
                # Get column names
                columns = result.keys()
                
                for idx, row in enumerate(result):
                    data = dict(zip(columns, row))
                    # Convert all values to string
                    data = {str(k): str(v) if v is not None else "" for k, v in data.items()}
                    
                    yield DataRow(
                        data=data,
                        row_number=idx + 1,
                        source_name=f"{config.get('dialect', 'db')}:{config.get('database', '')}",
                    )
                    
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            raise
    
    def test_connection(self, config: dict) -> tuple[bool, str]:
        """Test koneksi ke database."""
        from sqlalchemy import create_engine, text
        
        try:
            conn_string = self._build_connection_string(config)
            engine = create_engine(conn_string)
            
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            return True, "Connection successful"
            
        except Exception as e:
            return False, str(e)