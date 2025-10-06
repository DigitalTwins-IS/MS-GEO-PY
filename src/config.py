"""
Configuración del microservicio MS-GEO-PY
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # API Configuration
    APP_NAME: str = "MS-GEO-PY - Geographic Service"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1/geo"
    DEBUG: bool = False
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://dgt_user:dgt_pass@localhost:5437/digital_twins_db"
    
    # JWT Configuration (para validar tokens del MS-AUTH)
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    
    # CORS Configuration
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost"
    ]
    
    # Service Configuration
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8000
    
    # Geographic Configuration
    DEFAULT_COUNTRY: str = "Colombia"
    DEFAULT_SRID: int = 4326  # WGS84 - Sistema de coordenadas mundial
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instancia global de configuración
settings = Settings()

