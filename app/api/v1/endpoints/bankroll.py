from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.bankroll_service import BankrollService

router = APIRouter()


@router.get("/summary", response_model=Dict[str, Any])
async def get_bankroll_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener resumen del bankroll del usuario"""
    bankroll_service = BankrollService(db)
    
    summary = bankroll_service.get_bankroll_summary(current_user.id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bankroll configuration not found"
        )
    
    return summary


@router.put("/config")
async def update_bankroll_config(
    config_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar configuración del bankroll"""
    bankroll_service = BankrollService(db)
    
    config = bankroll_service.get_user_bankroll_config(current_user.id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bankroll configuration not found"
        )
    
    # Actualizar campos permitidos
    if "max_bet_percentage" in config_data:
        config.max_bet_percentage = config_data["max_bet_percentage"]
    
    if "min_bet_amount" in config_data:
        config.min_bet_amount = config_data["min_bet_amount"]
    
    if "max_bet_amount" in config_data:
        config.max_bet_amount = config_data["max_bet_amount"]
    
    if "currency" in config_data:
        config.currency = config_data["currency"]
    
    db.commit()
    db.refresh(config)
    
    return {"message": "Bankroll configuration updated successfully"}


class AmountPayload(BaseModel):
    amount: float


@router.post("/deposit")
async def deposit_funds(
    payload: AmountPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Depositar fondos al bankroll"""
    bankroll_service = BankrollService(db)
    
    config = bankroll_service.get_user_bankroll_config(current_user.id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bankroll configuration not found"
        )
    
    # Crear transacción de depósito
    from app.models.bankroll import BankrollTransaction, TransactionType
    
    amount = payload.amount
    transaction = BankrollTransaction(
        user_id=current_user.id,
        transaction_type=TransactionType.DEPOSIT,
        amount=amount,
        balance_before=config.current_amount,
        balance_after=config.current_amount + amount,
        description=f"Deposit: ${amount}"
    )
    
    # Actualizar bankroll
    config.current_amount += amount
    config.initial_amount += amount
    
    db.add(transaction)
    db.commit()
    
    return {"message": f"Successfully deposited ${amount}", "new_balance": config.current_amount}


@router.post("/withdraw")
async def withdraw_funds(
    payload: AmountPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retirar fondos del bankroll"""
    bankroll_service = BankrollService(db)
    
    config = bankroll_service.get_user_bankroll_config(current_user.id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bankroll configuration not found"
        )
    
    # Verificar fondos suficientes
    amount = payload.amount
    if amount > config.current_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds for withdrawal"
        )
    
    # Crear transacción de retiro
    from app.models.bankroll import BankrollTransaction, TransactionType
    
    transaction = BankrollTransaction(
        user_id=current_user.id,
        transaction_type=TransactionType.WITHDRAWAL,
        amount=-amount,
        balance_before=config.current_amount,
        balance_after=config.current_amount - amount,
        description=f"Withdrawal: ${amount}"
    )
    
    # Actualizar bankroll
    config.current_amount -= amount
    
    db.add(transaction)
    db.commit()
    
    return {"message": f"Successfully withdrawn ${amount}", "new_balance": config.current_amount}