from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from app.models.bankroll import TransactionType


class BankrollConfigBase(BaseModel):
    """Base schema para configuración de bankroll"""
    initial_amount: Decimal = Field(..., gt=0)
    max_bet_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    min_bet_amount: Optional[Decimal] = Field(None, ge=0)
    max_bet_amount: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=3)


class BankrollConfigCreate(BankrollConfigBase):
    """Schema para crear configuración de bankroll"""
    pass


class BankrollConfigResponse(BankrollConfigBase):
    """Schema de respuesta para configuración de bankroll"""
    id: int
    user_id: int
    current_amount: Decimal
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class BankrollTransactionBase(BaseModel):
    """Base schema para transacción de bankroll"""
    transaction_type: TransactionType
    amount: Decimal = Field(...)
    balance_before: Decimal = Field(...)
    balance_after: Decimal = Field(...)
    description: Optional[str] = Field(None, max_length=1000)
    related_bet_id: Optional[int] = None


class BankrollTransactionResponse(BankrollTransactionBase):
    """Schema de respuesta para transacción de bankroll"""
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class BankrollSummary(BaseModel):
    """Schema para resumen de bankroll"""
    current_amount: Decimal
    initial_amount: Decimal
    profit_loss: Decimal
    profit_loss_percentage: float
    total_deposits: Decimal
    total_withdrawals: Decimal
    total_bet_placed: Decimal
    total_bet_won: Decimal
    total_bet_lost: Decimal
    total_bet_void: Decimal
    recent_transactions: list[BankrollTransactionResponse]