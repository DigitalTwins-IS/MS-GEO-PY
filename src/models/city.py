"""
Modelo de Ciudad
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class City(Base):
    """Modelo de Ciudad"""
    
    __tablename__ = "cities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    country = Column(String(100), default="Colombia", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    zones = relationship("Zone", back_populates="city", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<City(id={self.id}, name={self.name}, country={self.country})>"

