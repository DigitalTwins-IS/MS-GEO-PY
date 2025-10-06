"""
Schemas Geográficos
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


# ========== CITY SCHEMAS ==========

class CityBase(BaseModel):
    """Schema base de Ciudad"""
    name: str = Field(..., min_length=2, max_length=255, description="Nombre de la ciudad")
    country: str = Field(default="Colombia", max_length=100, description="País")


class CityCreate(CityBase):
    """Schema para crear ciudad"""
    pass
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Bogotá",
                "country": "Colombia"
            }
        }


class CityUpdate(BaseModel):
    """Schema para actualizar ciudad"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    country: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class CityResponse(CityBase):
    """Schema para respuesta de ciudad"""
    id: int = Field(..., description="ID de la ciudad")
    is_active: bool = Field(..., description="Estado activo")
    created_at: datetime = Field(..., description="Fecha de creación")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Bogotá",
                "country": "Colombia",
                "is_active": True,
                "created_at": "2025-10-02T00:00:00Z"
            }
        }


# ========== ZONE SCHEMAS ==========

class ZoneBase(BaseModel):
    """Schema base de Zona"""
    name: str = Field(..., min_length=2, max_length=255, description="Nombre de la zona")
    city_id: int = Field(..., gt=0, description="ID de la ciudad")
    color: str = Field(default="#3498db", pattern=r"^#[0-9A-Fa-f]{6}$", description="Color en formato hexadecimal")
    description: Optional[str] = Field(None, description="Descripción de la zona")
    
    @field_validator('color')
    @classmethod
    def validate_color(cls, v):
        """Valida que el color sea hexadecimal válido"""
        if not v.startswith('#'):
            raise ValueError('El color debe comenzar con #')
        if len(v) != 7:
            raise ValueError('El color debe tener formato #RRGGBB')
        return v.upper()


class ZoneCreate(ZoneBase):
    """Schema para crear zona"""
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Norte",
                "city_id": 1,
                "color": "#e74c3c",
                "description": "Zona norte de Bogotá - Chapinero, Usaquén"
            }
        }


class ZoneUpdate(BaseModel):
    """Schema para actualizar zona"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    city_id: Optional[int] = Field(None, gt=0)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ZoneResponse(ZoneBase):
    """Schema para respuesta de zona"""
    id: int = Field(..., description="ID de la zona")
    is_active: bool = Field(..., description="Estado activo")
    created_at: datetime = Field(..., description="Fecha de creación")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Norte",
                "city_id": 1,
                "color": "#E74C3C",
                "description": "Zona norte de Bogotá",
                "is_active": True,
                "created_at": "2025-10-02T00:00:00Z"
            }
        }


class ZoneWithCityResponse(ZoneResponse):
    """Schema de zona con información de ciudad"""
    city_name: str = Field(..., description="Nombre de la ciudad")
    city_country: str = Field(..., description="País de la ciudad")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Norte",
                "city_id": 1,
                "color": "#E74C3C",
                "description": "Zona norte de Bogotá",
                "is_active": True,
                "created_at": "2025-10-02T00:00:00Z",
                "city_name": "Bogotá",
                "city_country": "Colombia"
            }
        }


class CityWithZonesResponse(CityResponse):
    """Schema de ciudad con sus zonas"""
    zones: List[ZoneResponse] = Field(default_factory=list, description="Zonas de la ciudad")
    total_zones: int = Field(..., description="Total de zonas")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Bogotá",
                "country": "Colombia",
                "is_active": True,
                "created_at": "2025-10-02T00:00:00Z",
                "zones": [
                    {
                        "id": 1,
                        "name": "Norte",
                        "city_id": 1,
                        "color": "#E74C3C",
                        "description": "Zona norte",
                        "is_active": True,
                        "created_at": "2025-10-02T00:00:00Z"
                    }
                ],
                "total_zones": 1
            }
        }


# ========== COORDINATE SCHEMAS ==========

class CoordinateValidation(BaseModel):
    """Schema para validar coordenadas geográficas"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitud (-90 a 90)")
    longitude: float = Field(..., ge=-180, le=180, description="Longitud (-180 a 180)")
    
    @field_validator('latitude')
    @classmethod
    def validate_latitude_colombia(cls, v):
        """Valida que la latitud esté dentro del rango de Colombia"""
        # Colombia: aproximadamente entre -4.23 y 12.46 de latitud
        if not (-5 <= v <= 13):
            raise ValueError('La latitud debe estar entre -5 y 13 (rango de Colombia)')
        return v
    
    @field_validator('longitude')
    @classmethod
    def validate_longitude_colombia(cls, v):
        """Valida que la longitud esté dentro del rango de Colombia"""
        # Colombia: aproximadamente entre -79.00 y -66.85 de longitud
        if not (-80 <= v <= -66):
            raise ValueError('La longitud debe estar entre -80 y -66 (rango de Colombia)')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 4.6097100,
                "longitude": -74.0817500
            }
        }


class CoordinateResponse(CoordinateValidation):
    """Schema de respuesta de coordenadas validadas"""
    is_valid: bool = Field(default=True, description="Indica si las coordenadas son válidas")
    country: str = Field(default="Colombia", description="País detectado")
    
    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 4.6097100,
                "longitude": -74.0817500,
                "is_valid": True,
                "country": "Colombia"
            }
        }


# ========== HEALTH SCHEMAS ==========

class HealthResponse(BaseModel):
    """Schema para health check"""
    status: str = Field(..., description="Estado del servicio")
    service: str = Field(..., description="Nombre del servicio")
    version: str = Field(..., description="Versión del servicio")
    database: str = Field(..., description="Estado de la base de datos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "MS-GEO-PY",
                "version": "1.0.0",
                "database": "connected"
            }
        }

