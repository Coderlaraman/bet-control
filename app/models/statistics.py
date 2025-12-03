from sqlalchemy import Column, Integer, ForeignKey, Numeric, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.session import Base


class SportStatistics(Base):
    __tablename__ = "sport_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    sport_id = Column(Integer, ForeignKey("sports.id"), nullable=False)
    total_bets = Column(Integer, default=0)
    won_bets = Column(Integer, default=0)
    lost_bets = Column(Integer, default=0)
    void_bets = Column(Integer, default=0)
    total_staked = Column(Numeric(15, 2), default=0.00)
    total_profit = Column(Numeric(15, 2), default=0.00)
    win_rate = Column(Numeric(5, 2), default=0.00)
    roi = Column(Numeric(5, 2), default=0.00)  # Return on Investment
    average_odds = Column(Numeric(6, 2), default=0.00)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="sport_statistics")
    sport = relationship("Sport", back_populates="sport_statistics")
    
    def __repr__(self):
        return f"<SportStatistics(user_id={self.user_id}, sport_id={self.sport_id})>"
    
    @property
    def total_settled_bets(self):
        """Total de apuestas resueltas"""
        return self.won_bets + self.lost_bets + self.void_bets
    
    @property
    def actual_win_rate(self):
        """Calcular win rate real"""
        if self.total_settled_bets > 0:
            return (self.won_bets / self.total_settled_bets) * 100
        return 0.0
    
    @property
    def actual_roi(self):
        """Calcular ROI real"""
        if float(self.total_staked) > 0:
            return (float(self.total_profit) / float(self.total_staked)) * 100
        return 0.0


class LeagueStatistics(Base):
    __tablename__ = "league_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    total_bets = Column(Integer, default=0)
    won_bets = Column(Integer, default=0)
    lost_bets = Column(Integer, default=0)
    void_bets = Column(Integer, default=0)
    total_staked = Column(Numeric(15, 2), default=0.00)
    total_profit = Column(Numeric(15, 2), default=0.00)
    win_rate = Column(Numeric(5, 2), default=0.00)
    roi = Column(Numeric(5, 2), default=0.00)
    average_odds = Column(Numeric(6, 2), default=0.00)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="league_statistics")
    league = relationship("League", back_populates="league_statistics")
    
    def __repr__(self):
        return f"<LeagueStatistics(user_id={self.user_id}, league_id={self.league_id})>"
    
    @property
    def total_settled_bets(self):
        """Total de apuestas resueltas"""
        return self.won_bets + self.lost_bets + self.void_bets
    
    @property
    def actual_win_rate(self):
        """Calcular win rate real"""
        if self.total_settled_bets > 0:
            return (self.won_bets / self.total_settled_bets) * 100
        return 0.0
    
    @property
    def actual_roi(self):
        """Calcular ROI real"""
        if float(self.total_staked) > 0:
            return (float(self.total_profit) / float(self.total_staked)) * 100
        return 0.0