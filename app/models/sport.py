from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base


class Sport(Base):
    __tablename__ = "sports"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    code = Column(String(10), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relaciones
    leagues = relationship("League", back_populates="sport")
    bets = relationship("Bet", back_populates="sport")
    markets = relationship("Market", back_populates="sport")
    sport_statistics = relationship("SportStatistics", back_populates="sport")
    
    def __repr__(self):
        return f"<Sport(name='{self.name}', code='{self.code}')>"


class Country(Base):
    __tablename__ = "countries"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    code = Column(String(3), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relaciones
    leagues = relationship("League", back_populates="country")
    bets = relationship("Bet", back_populates="country")
    
    def __repr__(self):
        return f"<Country(name='{self.name}', code='{self.code}')>"


class League(Base):
    __tablename__ = "leagues"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"))
    sport_id = Column(Integer, ForeignKey("sports.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relaciones
    country = relationship("Country", back_populates="leagues")
    sport = relationship("Sport", back_populates="leagues")
    bets = relationship("Bet", back_populates="league")
    league_statistics = relationship("LeagueStatistics", back_populates="league")
    
    def __repr__(self):
        return f"<League(name='{self.name}')>"
    
    @property
    def full_name(self):
        """Nombre completo incluyendo país"""
        if self.country:
            return f"{self.name} ({self.country.name})"
        return self.name