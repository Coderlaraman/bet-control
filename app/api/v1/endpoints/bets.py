from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from loguru import logger

from app.db.session import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.bet import Bet, BetStatus, ParlayBet, ParlayStatus
from app.schemas.bet import BetCreate, BetResponse, BetUpdate, ParlayBetCreate, ParlayBetResponse
from app.services.bet_service import BetService
from app.services.bankroll_service import BankrollService

router = APIRouter()


@router.post("/", response_model=BetResponse, status_code=status.HTTP_201_CREATED)
async def create_bet(
    bet_data: BetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Crear una nueva apuesta"""
    try:
        bet_service = BetService(db)
        bankroll_service = BankrollService(db)
        
        # Validar y deducir del bankroll
        bankroll_service.validate_bet_amount(current_user.id, bet_data.stake)
        
        # Crear apuesta
        bet = bet_service.create_bet(current_user.id, bet_data)
        
        # Deducir del bankroll
        bankroll_service.place_bet_deduction(current_user.id, bet.id, bet_data.stake)
        
        logger.info(f"Bet created: User {current_user.id}, Bet {bet.id}")
        return bet
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating bet: {e}")
        raise HTTPException(status_code=500, detail="Error creating bet")


@router.post("/parlay", response_model=ParlayBetResponse, status_code=status.HTTP_201_CREATED)
async def create_parlay_bet(
    parlay_data: ParlayBetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Crear una apuesta combinada"""
    try:
        bet_service = BetService(db)
        bankroll_service = BankrollService(db)
        
        # Validar y deducir del bankroll
        bankroll_service.validate_bet_amount(current_user.id, parlay_data.total_stake)
        
        # Crear apuesta combinada
        parlay = bet_service.create_parlay_bet(current_user.id, parlay_data)
        
        # Deducir del bankroll
        bankroll_service.place_bet_deduction(current_user.id, parlay.id, parlay_data.total_stake)
        
        logger.info(f"Parlay bet created: User {current_user.id}, Parlay {parlay.id}")
        return parlay
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating parlay bet: {e}")
        raise HTTPException(status_code=500, detail="Error creating parlay bet")


@router.get("/", response_model=List[BetResponse])
async def get_bets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None, description="Filter by bet status"),
    sport_id: Optional[int] = Query(None, description="Filter by sport"),
    league_id: Optional[int] = Query(None, description="Filter by league"),
    date_from: Optional[str] = Query(None, description="Filter by date from (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter by date to (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener lista de apuestas del usuario"""
    bet_service = BetService(db)
    
    bets = bet_service.get_user_bets(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        status=status,
        sport_id=sport_id,
        league_id=league_id,
        date_from=date_from,
        date_to=date_to
    )
    
    return bets


@router.get("/parlays", response_model=List[ParlayBetResponse])
async def get_parlay_bets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None, description="Filter by parlay status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener lista de apuestas combinadas del usuario"""
    bet_service = BetService(db)
    
    parlays = bet_service.get_user_parlay_bets(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        status=status
    )
    
    return parlays


@router.get("/{bet_id}", response_model=BetResponse)
async def get_bet(
    bet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener detalles de una apuesta específica"""
    bet_service = BetService(db)
    
    bet = bet_service.get_bet_by_id(bet_id)
    if not bet or bet.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bet not found")
    
    return bet


@router.put("/{bet_id}", response_model=BetResponse)
async def update_bet(
    bet_id: int,
    bet_data: BetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar una apuesta (solo ciertos campos)"""
    bet_service = BetService(db)
    bankroll_service = BankrollService(db)
    
    bet = bet_service.get_bet_by_id(bet_id)
    if not bet or bet.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bet not found")
    
    # Si se está actualizando el estado, procesar el bankroll
    if bet_data.status and bet_data.status != bet.status:
        old_status = bet.status
        new_status = bet_data.status
        
        # Actualizar apuesta
        updated_bet = bet_service.update_bet(bet_id, bet_data)
        
        # Procesar bankroll solo si el estado cambió a settled
        if new_status in [BetStatus.WON, BetStatus.LOST, BetStatus.VOID]:
            bankroll_service.process_bet_settlement(updated_bet)
        
        logger.info(f"Bet status updated: User {current_user.id}, Bet {bet_id}, "
                   f"{old_status} -> {new_status}")
        
        return updated_bet
    
    # Actualizar otros campos sin cambiar estado
    return bet_service.update_bet(bet_id, bet_data)


@router.delete("/{bet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bet(
    bet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Eliminar una apuesta (solo si está pendiente)"""
    bet_service = BetService(db)
    bankroll_service = BankrollService(db)
    
    bet = bet_service.get_bet_by_id(bet_id)
    if not bet or bet.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bet not found")
    
    if bet.status != BetStatus.PENDING:
        raise HTTPException(status_code=400, detail="Can only delete pending bets")
    
    # Devolver stake al bankroll
    bankroll_service.settle_bet_void(current_user.id, bet_id, bet.stake)
    
    # Eliminar apuesta
    bet_service.delete_bet(bet_id)
    
    logger.info(f"Bet deleted: User {current_user.id}, Bet {bet_id}")


@router.get("/summary/stats")
async def get_betting_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener estadísticas generales de apuestas del usuario"""
    bet_service = BetService(db)
    
    stats = bet_service.get_user_betting_stats(current_user.id)
    
    return stats