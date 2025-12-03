from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.session import Base

class Fixture(Base):
    """
    Almacena la información de partidos obtenidos de la API.
    Se usa para caché y análisis histórico.
    """
    __tablename__ = "fixtures"

    id = Column(String(20), primary_key=True)  # Usaremos el ID de API-Football (ej. "f123456")
    external_id = Column(Integer, unique=True, index=True) # ID numérico original de la API
    
    sport_id = Column(Integer, ForeignKey("sports.id"), nullable=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=True)
    
    home_team = Column(String(100), nullable=False)
    away_team = Column(String(100), nullable=False)
    
    event_date = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), default="NS") # NS: Not Started, FT: Full Time, etc.
    
    # Marcador final (para entrenamiento de IA)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    
    # Datos JSON crudos o procesados para análisis
    home_stats = Column(JSON, nullable=True)
    away_stats = Column(JSON, nullable=True)
    h2h_data = Column(JSON, nullable=True)
    
    # Resultado del análisis de IA
    prediction_data = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    league = relationship("League")
    sport = relationship("Sport")

    def __repr__(self):
        return f"<Fixture(id='{self.id}', {self.home_team} vs {self.away_team}, date='{self.event_date}')>"
