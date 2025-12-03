from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.db.session import Base


class UserRole(str, enum.Enum):
    """Roles de usuario en el sistema"""
    ADMIN = "admin"
    USER = "user"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    bankroll_config = relationship("BankrollConfig", back_populates="user", uselist=False)
    bets = relationship("Bet", back_populates="user")
    parlay_bets = relationship("ParlayBet", back_populates="user")
    bankroll_transactions = relationship("BankrollTransaction", back_populates="user")
    sport_statistics = relationship("SportStatistics", back_populates="user")
    league_statistics = relationship("LeagueStatistics", back_populates="user")
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def display_name(self):
        return self.full_name or self.username