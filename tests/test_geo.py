"""
Tests para el microservicio MS-GEO-PY
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.models import Base, get_db, City, Zone

# Base de datos en memoria para tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override de la dependency get_db para tests"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Configurar base de datos para cada test"""
    Base.metadata.create_all(bind=engine)
    
    # Crear datos de prueba
    db = TestingSessionLocal()
    
    # Crear ciudades
    city1 = City(name="Bogotá", country="Colombia", is_active=True)
    city2 = City(name="Medellín", country="Colombia", is_active=True)
    db.add_all([city1, city2])
    db.commit()
    
    # Crear zonas
    zone1 = Zone(name="Norte", city_id=1, color="#E74C3C", description="Zona norte", is_active=True)
    zone2 = Zone(name="Centro", city_id=1, color="#F39C12", description="Zona centro", is_active=True)
    zone3 = Zone(name="Sur", city_id=1, color="#27AE60", description="Zona sur", is_active=True)
    db.add_all([zone1, zone2, zone3])
    db.commit()
    db.close()
    
    yield
    
    Base.metadata.drop_all(bind=engine)


class TestHealth:
    """Tests de health check"""
    
    def test_health_check(self):
        """Test del health check"""
        response = client.get("/api/v1/geo/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]
        assert "service" in data
        assert "version" in data
    
    def test_root_redirect(self):
        """Test de redirección de raíz"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/docs"


class TestCities:
    """Tests de ciudades"""
    
    def test_get_cities(self):
        """Test de listar ciudades"""
        response = client.get("/api/v1/geo/cities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        assert data[0]["name"] == "Bogotá"
    
    def test_get_cities_with_pagination(self):
        """Test de listar ciudades con paginación"""
        response = client.get("/api/v1/geo/cities?skip=0&limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
    
    def test_get_cities_filter_active(self):
        """Test de filtrar ciudades activas"""
        response = client.get("/api/v1/geo/cities?is_active=true")
        assert response.status_code == 200
        data = response.json()
        assert all(city["is_active"] for city in data)
    
    def test_get_city_with_zones(self):
        """Test de obtener ciudad con zonas"""
        response = client.get("/api/v1/geo/cities/1")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Bogotá"
        assert "zones" in data
        assert "total_zones" in data
        assert data["total_zones"] == 3
        assert len(data["zones"]) == 3
    
    def test_get_city_not_found(self):
        """Test de ciudad no encontrada"""
        response = client.get("/api/v1/geo/cities/999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestZones:
    """Tests de zonas"""
    
    def test_get_zones(self):
        """Test de listar zonas"""
        response = client.get("/api/v1/geo/zones")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3
        assert "city_name" in data[0]
        assert "city_country" in data[0]
    
    def test_get_zones_by_city(self):
        """Test de filtrar zonas por ciudad"""
        response = client.get("/api/v1/geo/zones?city_id=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(zone["city_id"] == 1 for zone in data)
    
    def test_get_zones_with_pagination(self):
        """Test de listar zonas con paginación"""
        response = client.get("/api/v1/geo/zones?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_get_zone_by_id(self):
        """Test de obtener zona por ID"""
        response = client.get("/api/v1/geo/zones/1")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Norte"
        assert data["city_name"] == "Bogotá"
        assert data["color"] == "#E74C3C"
    
    def test_get_zone_not_found(self):
        """Test de zona no encontrada"""
        response = client.get("/api/v1/geo/zones/999")
        assert response.status_code == 404


class TestCoordinates:
    """Tests de coordenadas"""
    
    def test_validate_coordinates_valid(self):
        """Test de validar coordenadas válidas"""
        response = client.post(
            "/api/v1/geo/coordinates/validate",
            json={
                "latitude": 4.6097100,
                "longitude": -74.0817500
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["country"] == "Colombia"
    
    def test_validate_coordinates_out_of_colombia_range(self):
        """Test de coordenadas fuera del rango de Colombia"""
        response = client.post(
            "/api/v1/geo/coordinates/validate",
            json={
                "latitude": 40.7128,  # Nueva York
                "longitude": -74.0060
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_validate_coordinates_invalid_latitude(self):
        """Test de latitud inválida"""
        response = client.post(
            "/api/v1/geo/coordinates/validate",
            json={
                "latitude": 100,  # Fuera de rango
                "longitude": -74.0
            }
        )
        assert response.status_code == 422
    
    def test_validate_coordinates_invalid_longitude(self):
        """Test de longitud inválida"""
        response = client.post(
            "/api/v1/geo/coordinates/validate",
            json={
                "latitude": 4.6,
                "longitude": -200  # Fuera de rango
            }
        )
        assert response.status_code == 422


class TestSchemas:
    """Tests de schemas y validación"""
    
    def test_zone_color_validation(self):
        """Test de validación de color hexadecimal"""
        from src.schemas import ZoneCreate
        
        # Color válido
        zone = ZoneCreate(
            name="Test",
            city_id=1,
            color="#3498DB"
        )
        assert zone.color == "#3498DB"
        
        # Color inválido debe fallar
        with pytest.raises(ValueError):
            ZoneCreate(
                name="Test",
                city_id=1,
                color="blue"  # No es hexadecimal
            )
    
    def test_coordinate_validation(self):
        """Test de validación de coordenadas"""
        from src.schemas import CoordinateValidation
        
        # Coordenadas válidas
        coords = CoordinateValidation(
            latitude=4.6097100,
            longitude=-74.0817500
        )
        assert coords.latitude == 4.6097100
        
        # Latitud fuera de rango de Colombia
        with pytest.raises(ValueError):
            CoordinateValidation(
                latitude=40.0,  # Fuera de Colombia
                longitude=-74.0
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

