from typing import Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from loguru import logger

from app.models.bankroll import BankrollConfig, BankrollTransaction, TransactionType
from app.models.bet import Bet, BetStatus, ParlayBet, ParlayStatus
from app.core.config import settings
from app.core.exceptions import InsufficientFundsError, InvalidBetAmountError


class BankrollService:
    """Servicio para gestionar el bankroll automáticamente"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_bankroll_config(self, user_id: int) -> Optional[BankrollConfig]:
        """Obtener configuración de bankroll del usuario"""
        return self.db.query(BankrollConfig).filter(BankrollConfig.user_id == user_id).first()
    
    def create_bankroll_config(self, user_id: int, initial_amount: Decimal) -> BankrollConfig:
        """Crear configuración inicial de bankroll"""
        config = BankrollConfig(
            user_id=user_id,
            initial_amount=initial_amount,
            current_amount=initial_amount,
            max_bet_percentage=settings.DEFAULT_MAX_BET_PERCENTAGE,
            min_bet_amount=settings.DEFAULT_MIN_BET_AMOUNT,
            max_bet_amount=settings.DEFAULT_MAX_BET_AMOUNT
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        
        logger.info(f"Bankroll config created for user {user_id} with amount {initial_amount}")
        return config
    
    def validate_bet_amount(self, user_id: int, stake: Decimal) -> bool:
        """Validar si el monto de la apuesta es permitido"""
        config = self.get_user_bankroll_config(user_id)
        if not config:
            raise ValueError("User bankroll configuration not found")
        
        # Verificar fondos suficientes
        if stake > config.current_amount:
            raise InsufficientFundsError(
                f"Insufficient funds. Current bankroll: {config.current_amount}, "
                f"attempted stake: {stake}"
            )
        
        # Verificar mínimo permitido
        if stake < config.min_bet_amount:
            raise InvalidBetAmountError(
                f"Bet amount {stake} is below minimum allowed: {config.min_bet_amount}"
            )
        
        # Verificar máximo permitido por porcentaje de bankroll
        max_allowed = config.max_bet_allowed
        if stake > max_allowed:
            raise InvalidBetAmountError(
                f"Bet amount {stake} exceeds maximum allowed: {max_allowed} "
                f"({config.max_bet_percentage}% of bankroll)"
            )
        
        # Verificar máximo absoluto
        if stake > config.max_bet_amount:
            raise InvalidBetAmountError(
                f"Bet amount {stake} exceeds maximum allowed: {config.max_bet_amount}"
            )
        
        return True
    
    def place_bet_deduction(self, user_id: int, bet_id: int, stake: Decimal) -> BankrollTransaction:
        """Deducir monto de apuesta del bankroll"""
        config = self.get_user_bankroll_config(user_id)
        if not config:
            raise ValueError("User bankroll configuration not found")
        
        # Validar monto
        self.validate_bet_amount(user_id, stake)
        
        # Crear transacción
        transaction = BankrollTransaction(
            user_id=user_id,
            transaction_type=TransactionType.BET_PLACED,
            amount=-stake,  # Negativo porque es una deducción
            balance_before=config.current_amount,
            balance_after=config.current_amount - stake,
            related_bet_id=bet_id,
            description=f"Bet placed - Stake: {stake}"
        )
        
        # Actualizar bankroll
        config.current_amount -= stake
        
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        
        logger.info(f"Bet deduction: User {user_id}, Bet {bet_id}, Amount {stake}")
        return transaction
    
    def settle_bet_win(self, user_id: int, bet_id: int, win_amount: Decimal) -> BankrollTransaction:
        """Procesar apuesta ganadora"""
        config = self.get_user_bankroll_config(user_id)
        if not config:
            raise ValueError("User bankroll configuration not found")
        
        # Crear transacción
        transaction = BankrollTransaction(
            user_id=user_id,
            transaction_type=TransactionType.BET_WON,
            amount=win_amount,
            balance_before=config.current_amount,
            balance_after=config.current_amount + win_amount,
            related_bet_id=bet_id,
            description=f"Bet won - Winnings: {win_amount}"
        )
        
        # Actualizar bankroll
        config.current_amount += win_amount
        
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        
        logger.info(f"Bet win: User {user_id}, Bet {bet_id}, Amount {win_amount}")
        return transaction
    
    def settle_bet_loss(self, user_id: int, bet_id: int) -> BankrollTransaction:
        """Procesar apuesta perdedora"""
        # No se hace ninguna transacción adicional ya que la deducción ya se hizo al colocar la apuesta
        logger.info(f"Bet loss: User {user_id}, Bet {bet_id}")
        return None
    
    def settle_bet_void(self, user_id: int, bet_id: int, stake: Decimal) -> BankrollTransaction:
        """Procesar apuesta anulada"""
        config = self.get_user_bankroll_config(user_id)
        if not config:
            raise ValueError("User bankroll configuration not found")
        
        # Crear transacción de devolución
        transaction = BankrollTransaction(
            user_id=user_id,
            transaction_type=TransactionType.BET_VOID,
            amount=stake,
            balance_before=config.current_amount,
            balance_after=config.current_amount + stake,
            related_bet_id=bet_id,
            description=f"Bet void - Stake returned: {stake}"
        )
        
        # Actualizar bankroll
        config.current_amount += stake
        
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        
        logger.info(f"Bet void: User {user_id}, Bet {bet_id}, Stake returned {stake}")
        return transaction
    
    def process_bet_settlement(self, bet: Bet) -> Optional[BankrollTransaction]:
        """Procesar el resultado de una apuesta"""
        if bet.status == BetStatus.WON:
            return self.settle_bet_win(bet.user_id, bet.id, bet.result_amount)
        elif bet.status == BetStatus.LOST:
            return self.settle_bet_loss(bet.user_id, bet.id)
        elif bet.status == BetStatus.VOID:
            return self.settle_bet_void(bet.user_id, bet.id, bet.stake)
        
        return None
    
    def process_parlay_settlement(self, parlay: ParlayBet) -> Optional[BankrollTransaction]:
        """Procesar el resultado de una apuesta combinada"""
        if parlay.status == ParlayStatus.WON:
            return self.settle_bet_win(parlay.user_id, parlay.id, parlay.result_amount)
        elif parlay.status == ParlayStatus.LOST:
            return self.settle_bet_loss(parlay.user_id, parlay.id)
        elif parlay.status == ParlayStatus.VOID:
            return self.settle_bet_void(parlay.user_id, parlay.id, parlay.total_stake)
        
        return None
    
    def get_bankroll_summary(self, user_id: int) -> dict:
        """Obtener resumen del bankroll"""
        config = self.get_user_bankroll_config(user_id)
        if not config:
            return None
        
        # Calcular estadísticas adicionales
        transactions = self.db.query(BankrollTransaction).filter(
            BankrollTransaction.user_id == user_id
        ).order_by(BankrollTransaction.created_at.desc()).limit(10).all()
        
        return {
            "current_amount": float(config.current_amount),
            "initial_amount": float(config.initial_amount),
            "profit_loss": float(config.current_amount - config.initial_amount),
            "max_bet_allowed": float(config.max_bet_allowed),
            "min_bet_amount": float(config.min_bet_amount),
            "max_bet_amount": float(config.max_bet_amount),
            "max_bet_percentage": float(config.max_bet_percentage),
            "currency": config.currency,
            "recent_transactions": [
                {
                    "type": t.transaction_type.value,
                    "amount": float(t.amount),
                    "balance_before": float(t.balance_before),
                    "balance_after": float(t.balance_after),
                    "created_at": t.created_at.isoformat()
                }
                for t in transactions
            ]
        }