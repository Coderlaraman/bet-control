from sqlalchemy import Column, Integer, ForeignKey, Numeric, String, Text, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.db.session import Base


class TransactionType(enum.Enum):
    BET_PLACED = "bet_placed"
    BET_WON = "bet_won"
    BET_LOST = "bet_lost"
    BET_VOID = "bet_void"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    ADJUSTMENT = "adjustment"


class BankrollConfig(Base):
    __tablename__ = "bankroll_config"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    initial_amount = Column(Numeric(15, 2), nullable=False, default=0.00)
    current_amount = Column(Numeric(15, 2), nullable=False, default=0.00)
    max_bet_percentage = Column(Numeric(5, 2), default=5.00)  # 5% of bankroll
    min_bet_amount = Column(Numeric(10, 2), default=1.00)
    max_bet_amount = Column(Numeric(10, 2), default=1000.00)
    currency = Column(String(3), default="USD")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="bankroll_config")
    
    def __repr__(self):
        return f"<BankrollConfig(user_id={self.user_id}, current_amount={self.current_amount})>"
    
    @property
    def max_bet_allowed(self):
        """Calcular apuesta máxima permitida basada en porcentaje"""
        return float(self.current_amount) * (float(self.max_bet_percentage) / 100)


class BankrollTransaction(Base):
    __tablename__ = "bankroll_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    balance_before = Column(Numeric(15, 2), nullable=False)
    balance_after = Column(Numeric(15, 2), nullable=False)
    related_bet_id = Column(Integer, ForeignKey("bets.id"))
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="bankroll_transactions")
    related_bet = relationship("Bet")
    
    def __repr__(self):
        return f"<BankrollTransaction(user_id={self.user_id}, type={self.transaction_type}, amount={self.amount})>"
    
    @property
    def is_credit(self):
        """Determinar si es una transacción de crédito"""
        return self.transaction_type in [TransactionType.BET_WON, TransactionType.DEPOSIT]
    
    @property
    def is_debit(self):
        """Determinar si es una transacción de débito"""
        return self.transaction_type in [TransactionType.BET_PLACED, TransactionType.WITHDRAWAL]