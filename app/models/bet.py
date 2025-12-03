from sqlalchemy import Column, Integer, ForeignKey, String, Numeric, Text, DateTime, Enum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.db.session import Base


class BetStatus(enum.Enum):
    PENDING = "pending"
    WON = "won"
    LOST = "lost"
    VOID = "void"
    HALF_WON = "half_won"
    HALF_LOST = "half_lost"


class ParlayStatus(enum.Enum):
    PENDING = "pending"
    WON = "won"
    LOST = "lost"
    VOID = "void"


class BetType(Base):
    __tablename__ = "bet_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Relaciones
    bets = relationship("Bet", back_populates="bet_type")
    parlay_bets = relationship("ParlayBet", back_populates="bet_type")
    
    def __repr__(self):
        return f"<BetType(name='{self.name}')>"


class Market(Base):
    __tablename__ = "markets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(Text)
    sport_id = Column(Integer, ForeignKey("sports.id"))
    is_active = Column(Boolean, default=True)
    
    # Relaciones
    sport = relationship("Sport", back_populates="markets")
    bets = relationship("Bet", back_populates="market")
    
    def __repr__(self):
        return f"<Market(name='{self.name}', code='{self.code}')>"


class Bet(Base):
    __tablename__ = "bets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    bet_type_id = Column(Integer, ForeignKey("bet_types.id"), nullable=False)
    sport_id = Column(Integer, ForeignKey("sports.id"), nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"))
    league_id = Column(Integer, ForeignKey("leagues.id"))
    market_id = Column(Integer, ForeignKey("markets.id"))
    
    # Información del evento
    event_name = Column(String(200), nullable=False)
    event_date = Column(DateTime, nullable=False)
    event_time = Column(DateTime)
    home_team = Column(String(100))
    away_team = Column(String(100))
    
    # Detalles de la apuesta
    bet_description = Column(Text, nullable=False)  # Pick o descripción
    odds = Column(Numeric(8, 2), nullable=False)  # Cuota
    stake = Column(Numeric(10, 2), nullable=False)  # Monto apostado
    potential_win = Column(Numeric(12, 2), nullable=False)  # Ganancia potencial
    
    # Estado y resultados
    status = Column(Enum(BetStatus), default=BetStatus.PENDING)
    result_amount = Column(Numeric(12, 2))  # Monto final ganado/perdido
    settled_at = Column(DateTime)
    
    # Metadata
    bet_slip_id = Column(String(50))  # ID de RushBet si está disponible
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="bets")
    bet_type = relationship("BetType", back_populates="bets")
    sport = relationship("Sport", back_populates="bets")
    country = relationship("Country", back_populates="bets")
    league = relationship("League", back_populates="bets")
    market = relationship("Market", back_populates="bets")
    
    def __repr__(self):
        return f"<Bet(id={self.id}, user_id={self.user_id}, status={self.status})>"
    
    @property
    def is_settled(self):
        """Verificar si la apuesta está resuelta"""
        return self.status != BetStatus.PENDING
    
    @property
    def profit_loss(self):
        """Calcular ganancia/pérdida"""
        if self.status == BetStatus.WON:
            return float(self.result_amount or 0) - float(self.stake)
        elif self.status == BetStatus.LOST:
            return -float(self.stake)
        elif self.status == BetStatus.VOID:
            return 0.0
        return 0.0
    
    @property
    def roi_percentage(self):
        """Calcular ROI porcentual"""
        if float(self.stake) > 0:
            return (self.profit_loss / float(self.stake)) * 100
        return 0.0


class ParlayBet(Base):
    __tablename__ = "parlay_bets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    bet_type_id = Column(Integer, ForeignKey("bet_types.id"), nullable=False)
    total_odds = Column(Numeric(8, 2), nullable=False)
    total_stake = Column(Numeric(10, 2), nullable=False)
    potential_win = Column(Numeric(12, 2), nullable=False)
    status = Column(Enum(ParlayStatus), default=ParlayStatus.PENDING)
    result_amount = Column(Numeric(12, 2))
    settled_at = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="parlay_bets")
    bet_type = relationship("BetType", back_populates="parlay_bets")
    selections = relationship("ParlaySelection", back_populates="parlay_bet", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ParlayBet(id={self.id}, user_id={self.user_id}, status={self.status})>"
    
    @property
    def is_settled(self):
        """Verificar si la apuesta combinada está resuelta"""
        return self.status != ParlayStatus.PENDING
    
    @property
    def profit_loss(self):
        """Calcular ganancia/pérdida"""
        if self.status == ParlayStatus.WON:
            return float(self.result_amount or 0) - float(self.total_stake)
        elif self.status == ParlayStatus.LOST:
            return -float(self.total_stake)
        elif self.status == ParlayStatus.VOID:
            return 0.0
        return 0.0


class ParlaySelection(Base):
    __tablename__ = "parlay_selections"
    
    id = Column(Integer, primary_key=True, index=True)
    parlay_id = Column(Integer, ForeignKey("parlay_bets.id", ondelete="CASCADE"), nullable=False)
    sport_id = Column(Integer, ForeignKey("sports.id"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"))
    event_name = Column(String(200), nullable=False)
    event_date = Column(DateTime, nullable=False)
    market_id = Column(Integer, ForeignKey("markets.id"))
    selection = Column(String(200), nullable=False)  # Pick o selección
    odds = Column(Numeric(8, 2), nullable=False)
    status = Column(Enum(BetStatus), default=BetStatus.PENDING)
    
    # Relaciones
    parlay_bet = relationship("ParlayBet", back_populates="selections")
    sport = relationship("Sport")
    league = relationship("League")
    market = relationship("Market")
    
    def __repr__(self):
        return f"<ParlaySelection(id={self.id}, parlay_id={self.parlay_id}, status={self.status})>"
    
    @property
    def is_settled(self):
        """Verificar si la selección está resuelta"""
        return self.status != BetStatus.PENDING