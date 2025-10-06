"""
Schemas Pydantic para validación
"""
from .geo import (
    CityResponse,
    CityCreate,
    CityUpdate,
    ZoneResponse,
    ZoneCreate,
    ZoneUpdate,
    ZoneWithCityResponse,
    CityWithZonesResponse,
    HealthResponse,
    CoordinateValidation,
    CoordinateResponse
)

__all__ = [
    "CityResponse",
    "CityCreate",
    "CityUpdate",
    "ZoneResponse",
    "ZoneCreate",
    "ZoneUpdate",
    "ZoneWithCityResponse",
    "CityWithZonesResponse",
    "HealthResponse",
    "CoordinateValidation",
    "CoordinateResponse"
]

