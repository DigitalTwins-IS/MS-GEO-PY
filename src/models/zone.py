"""
Modelo de Zona
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class Zone(Base):
    """Modelo de Zona - Áreas dentro de una ciudad"""
    
    __tablename__ = "zones"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    city_id = Column(Integer, ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    color = Column(String(7), default="#3498db", nullable=False)  # Color hexadecimal
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    city = relationship("City", back_populates="zones")
    
    def __repr__(self):
        return f"<Zone(id={self.id}, name={self.name}, city_id={self.city_id}, color={self.color})>"

