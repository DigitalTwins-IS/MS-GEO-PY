"""
Router Geográfico
Endpoints: /cities, /zones, /coordinates
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional

from ..models import get_db, City, Zone
from ..schemas import (
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
from ..utils import get_current_user
from ..config import settings

router = APIRouter()


# ========== HEALTH CHECK ==========

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Verifica el estado del servicio y la conexión a base de datos",
    tags=["Health"]
)
async def health_check(db: Session = Depends(get_db)):
    """Health check del microservicio"""
    try:
        db.execute(text("SELECT 1"))
        database_status = "connected"
    except Exception as e:
        database_status = f"error: {str(e)}"
    
    return HealthResponse(
        status="healthy" if database_status == "connected" else "unhealthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        database=database_status
    )


# ========== CITIES ENDPOINTS ==========

@router.get(
    "/cities",
    response_model=List[CityResponse],
    summary="Listar ciudades",
    description="HU1: Obtiene lista de todas las ciudades disponibles",
    tags=["Ciudades"]
)
async def get_cities(
    skip: int = Query(0, ge=0, description="Registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    db: Session = Depends(get_db)
):
    """
    HU1: Como administrador, quiero ver las ciudades disponibles
    
    Returns:
        List[CityResponse]: Lista de ciudades
    """
    query = db.query(City)
    
    if is_active is not None:
        query = query.filter(City.is_active == is_active)
    
    cities = query.offset(skip).limit(limit).all()
    return cities


@router.get(
    "/cities/{city_id}",
    response_model=CityWithZonesResponse,
    summary="Obtener ciudad con zonas",
    description="HU1: Obtiene una ciudad específica con todas sus zonas",
    tags=["Ciudades"]
)
async def get_city_with_zones(
    city_id: int,
    db: Session = Depends(get_db)
):
    """
    HU1: Como administrador, quiero seleccionar una ciudad y ver sus zonas
    
    Args:
        city_id: ID de la ciudad
        
    Returns:
        CityWithZonesResponse: Ciudad con sus zonas
        
    Raises:
        HTTPException: Si la ciudad no existe
    """
    city = db.query(City).filter(City.id == city_id).first()
    
    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ciudad con ID {city_id} no encontrada"
        )
    
    # Obtener zonas activas de la ciudad
    zones = db.query(Zone).filter(
        Zone.city_id == city_id,
        Zone.is_active == True
    ).all()
    
    return CityWithZonesResponse(
        **city.__dict__,
        zones=[ZoneResponse.model_validate(z) for z in zones],
        total_zones=len(zones)
    )


@router.post(
    "/cities",
    response_model=CityResponse,
    summary="Crear ciudad",
    description="Crea una nueva ciudad (requiere autenticación)",
    tags=["Ciudades"],
    status_code=status.HTTP_201_CREATED
)
async def create_city(
    city_data: CityCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Crea una nueva ciudad en el sistema
    
    Args:
        city_data: Datos de la ciudad
        db: Sesión de base de datos
        current_user: Usuario autenticado
        
    Returns:
        CityResponse: Ciudad creada
        
    Raises:
        HTTPException: Si la ciudad ya existe
    """
    # Verificar que no exista
    existing = db.query(City).filter(City.name == city_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La ciudad '{city_data.name}' ya existe"
        )
    
    # Crear nueva ciudad
    new_city = City(**city_data.model_dump())
    db.add(new_city)
    db.commit()
    db.refresh(new_city)
    
    return new_city


@router.put(
    "/cities/{city_id}",
    response_model=CityResponse,
    summary="Actualizar ciudad",
    description="Actualiza los datos de una ciudad existente",
    tags=["Ciudades"]
)
async def update_city(
    city_id: int,
    city_data: CityUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Actualiza una ciudad existente
    
    Args:
        city_id: ID de la ciudad
        city_data: Datos a actualizar
        db: Sesión de base de datos
        current_user: Usuario autenticado
        
    Returns:
        CityResponse: Ciudad actualizada
        
    Raises:
        HTTPException: Si la ciudad no existe
    """
    city = db.query(City).filter(City.id == city_id).first()
    
    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ciudad con ID {city_id} no encontrada"
        )
    
    # Actualizar campos proporcionados
    update_data = city_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(city, field, value)
    
    db.commit()
    db.refresh(city)
    
    return city


# ========== ZONES ENDPOINTS ==========

@router.get(
    "/zones",
    response_model=List[ZoneWithCityResponse],
    summary="Listar zonas",
    description="HU1: Obtiene lista de todas las zonas con información de ciudad",
    tags=["Zonas"]
)
async def get_zones(
    city_id: Optional[int] = Query(None, description="Filtrar por ciudad"),
    skip: int = Query(0, ge=0, description="Registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    db: Session = Depends(get_db)
):
    """
    HU1: Como administrador, quiero ver las zonas disponibles
    
    Returns:
        List[ZoneWithCityResponse]: Lista de zonas con información de ciudad
    """
    query = db.query(Zone, City).join(City, Zone.city_id == City.id)
    
    if city_id is not None:
        query = query.filter(Zone.city_id == city_id)
    
    if is_active is not None:
        query = query.filter(Zone.is_active == is_active)
    
    zones = query.offset(skip).limit(limit).all()
    
    # Construir respuesta con información de ciudad
    result = []
    for zone, city in zones:
        zone_dict = {
            **zone.__dict__,
            "city_name": city.name,
            "city_country": city.country
        }
        result.append(ZoneWithCityResponse(**zone_dict))
    
    return result


@router.get(
    "/zones/{zone_id}",
    response_model=ZoneWithCityResponse,
    summary="Obtener zona",
    description="Obtiene una zona específica con información de su ciudad",
    tags=["Zonas"]
)
async def get_zone(
    zone_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene una zona por su ID
    
    Args:
        zone_id: ID de la zona
        
    Returns:
        ZoneWithCityResponse: Zona con información de ciudad
        
    Raises:
        HTTPException: Si la zona no existe
    """
    zone, city = db.query(Zone, City).join(
        City, Zone.city_id == City.id
    ).filter(Zone.id == zone_id).first() or (None, None)
    
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zona con ID {zone_id} no encontrada"
        )
    
    zone_dict = {
        **zone.__dict__,
        "city_name": city.name,
        "city_country": city.country
    }
    
    return ZoneWithCityResponse(**zone_dict)


@router.post(
    "/zones",
    response_model=ZoneResponse,
    summary="Crear zona",
    description="Crea una nueva zona en una ciudad (requiere autenticación)",
    tags=["Zonas"],
    status_code=status.HTTP_201_CREATED
)
async def create_zone(
    zone_data: ZoneCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Crea una nueva zona en una ciudad
    
    Args:
        zone_data: Datos de la zona
        db: Sesión de base de datos
        current_user: Usuario autenticado
        
    Returns:
        ZoneResponse: Zona creada
        
    Raises:
        HTTPException: Si la ciudad no existe o la zona ya existe
    """
    # Verificar que la ciudad existe
    city = db.query(City).filter(City.id == zone_data.city_id).first()
    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ciudad con ID {zone_data.city_id} no encontrada"
        )
    
    # Verificar que no exista la misma zona en la ciudad
    existing = db.query(Zone).filter(
        Zone.name == zone_data.name,
        Zone.city_id == zone_data.city_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La zona '{zone_data.name}' ya existe en {city.name}"
        )
    
    # Crear nueva zona
    new_zone = Zone(**zone_data.model_dump())
    db.add(new_zone)
    db.commit()
    db.refresh(new_zone)
    
    return new_zone


@router.put(
    "/zones/{zone_id}",
    response_model=ZoneResponse,
    summary="Actualizar zona",
    description="Actualiza los datos de una zona existente",
    tags=["Zonas"]
)
async def update_zone(
    zone_id: int,
    zone_data: ZoneUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Actualiza una zona existente
    
    Args:
        zone_id: ID de la zona
        zone_data: Datos a actualizar
        db: Sesión de base de datos
        current_user: Usuario autenticado
        
    Returns:
        ZoneResponse: Zona actualizada
        
    Raises:
        HTTPException: Si la zona no existe
    """
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zona con ID {zone_id} no encontrada"
        )
    
    # Actualizar campos proporcionados
    update_data = zone_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(zone, field, value)
    
    db.commit()
    db.refresh(zone)
    
    return zone


# ========== COORDINATES ENDPOINTS ==========

@router.post(
    "/coordinates/validate",
    response_model=CoordinateResponse,
    summary="Validar coordenadas",
    description="Valida que las coordenadas estén dentro del rango de Colombia",
    tags=["Coordenadas"]
)
async def validate_coordinates(coordinates: CoordinateValidation):
    """
    Valida coordenadas geográficas
    
    Args:
        coordinates: Latitud y longitud a validar
        
    Returns:
        CoordinateResponse: Coordenadas validadas
    """
    return CoordinateResponse(
        latitude=coordinates.latitude,
        longitude=coordinates.longitude,
        is_valid=True,
        country=settings.DEFAULT_COUNTRY
    )

