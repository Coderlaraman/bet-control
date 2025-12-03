from typing import List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from loguru import logger

from app.models.bet import Bet, BetStatus, ParlayBet, ParlayStatus, BetType, Market
from app.models.sport import Sport, Country, League
from app.models.user import User
from app.schemas.bet import BetCreate, BetUpdate, ParlayBetCreate


class BetService:
    """Servicio para gestionar apuestas"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_bet(self, user_id: int, bet_data: BetCreate) -> Bet:
        """Crear una nueva apuesta"""
        # Calcular ganancia potencial
        potential_win = float(bet_data.stake) * float(bet_data.odds)
        
        bet = Bet(
            user_id=user_id,
            bet_type_id=bet_data.bet_type_id,
            sport_id=bet_data.sport_id,
            country_id=bet_data.country_id,
            league_id=bet_data.league_id,
            market_id=bet_data.market_id,
            event_name=bet_data.event_name,
            event_date=bet_data.event_date,
            event_time=bet_data.event_time,
            home_team=bet_data.home_team,
            away_team=bet_data.away_team,
            bet_description=bet_data.bet_description,
            odds=bet_data.odds,
            stake=bet_data.stake,
            potential_win=potential_win,
            notes=bet_data.notes
        )
        
        self.db.add(bet)
        self.db.commit()
        self.db.refresh(bet)
        
        logger.info(f"Bet created: User {user_id}, Bet {bet.id}")
        return bet
    
    def create_parlay_bet(self, user_id: int, parlay_data: ParlayBetCreate) -> ParlayBet:
        """Crear una apuesta combinada"""
        parlay = ParlayBet(
            user_id=user_id,
            bet_type_id=parlay_data.bet_type_id,
            total_odds=parlay_data.total_odds,
            total_stake=parlay_data.total_stake,
            potential_win=parlay_data.potential_win
        )
        
        self.db.add(parlay)
        self.db.flush()  # Para obtener el ID
        
        # Crear selecciones
        for selection_data in parlay_data.selections:
            selection = ParlaySelection(
                parlay_id=parlay.id,
                sport_id=selection_data.sport_id,
                league_id=selection_data.league_id,
                event_name=selection_data.event_name,
                event_date=selection_data.event_date,
                market_id=selection_data.market_id,
                selection=selection_data.selection,
                odds=selection_data.odds
            )
            self.db.add(selection)
        
        self.db.commit()
        self.db.refresh(parlay)
        
        logger.info(f"Parlay bet created: User {user_id}, Parlay {parlay.id}")
        return parlay
    
    def get_bet_by_id(self, bet_id: int) -> Optional[Bet]:
        """Obtener apuesta por ID"""
        return self.db.query(Bet).filter(Bet.id == bet_id).first()
    
    def get_user_bets(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        sport_id: Optional[int] = None,
        league_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Bet]:
        """Obtener apuestas de un usuario con filtros"""
        query = self.db.query(Bet).filter(Bet.user_id == user_id)
        
        # Aplicar filtros
        if status:
            query = query.filter(Bet.status == status)
        
        if sport_id:
            query = query.filter(Bet.sport_id == sport_id)
        
        if league_id:
            query = query.filter(Bet.league_id == league_id)
        
        if date_from:
            try:
                from_date = datetime.strptime(date_from, "%Y-%m-%d")
                query = query.filter(Bet.created_at >= from_date)
            except ValueError:
                pass
        
        if date_to:
            try:
                to_date = datetime.strptime(date_to, "%Y-%m-%d")
                query = query.filter(Bet.created_at <= to_date)
            except ValueError:
                pass
        
        return query.order_by(Bet.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_user_parlay_bets(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None
    ) -> List[ParlayBet]:
        """Obtener apuestas combinadas de un usuario"""
        query = self.db.query(ParlayBet).filter(ParlayBet.user_id == user_id)
        
        if status:
            query = query.filter(ParlayBet.status == status)
        
        return query.order_by(ParlayBet.created_at.desc()).offset(skip).limit(limit).all()
    
    def update_bet(self, bet_id: int, bet_data: BetUpdate) -> Optional[Bet]:
        """Actualizar apuesta"""
        bet = self.get_bet_by_id(bet_id)
        if not bet:
            return None
        
        # Actualizar campos permitidos
        if bet_data.status is not None:
            bet.status = bet_data.status
            if bet_data.status in [BetStatus.WON, BetStatus.LOST, BetStatus.VOID]:
                bet.settled_at = datetime.utcnow()
        
        if bet_data.result_amount is not None:
            bet.result_amount = bet_data.result_amount
        
        if bet_data.notes is not None:
            bet.notes = bet_data.notes
        
        self.db.commit()
        self.db.refresh(bet)
        
        logger.info(f"Bet updated: Bet {bet_id}, Status: {bet_data.status}")
        return bet
    
    def delete_bet(self, bet_id: int) -> bool:
        """Eliminar apuesta (solo si está pendiente)"""
        bet = self.get_bet_by_id(bet_id)
        if not bet or bet.status != BetStatus.PENDING:
            return False
        
        self.db.delete(bet)
        self.db.commit()
        
        logger.info(f"Bet deleted: Bet {bet_id}")
        return True
    
    def get_user_betting_stats(self, user_id: int) -> dict:
        """Obtener estadísticas de apuestas del usuario"""
        # Total de apuestas por estado
        total_bets = self.db.query(Bet).filter(Bet.user_id == user_id).count()
        won_bets = self.db.query(Bet).filter(Bet.user_id == user_id, Bet.status == BetStatus.WON).count()
        lost_bets = self.db.query(Bet).filter(Bet.user_id == user_id, Bet.status == BetStatus.LOST).count()
        void_bets = self.db.query(Bet).filter(Bet.user_id == user_id, Bet.status == BetStatus.VOID).count()
        pending_bets = self.db.query(Bet).filter(Bet.user_id == user_id, Bet.status == BetStatus.PENDING).count()
        
        # Montos
        from sqlalchemy import func
        total_staked = self.db.query(func.sum(Bet.stake)).filter(Bet.user_id == user_id).scalar() or 0
        total_won = self.db.query(func.sum(Bet.result_amount)).filter(
            Bet.user_id == user_id, Bet.status == BetStatus.WON
        ).scalar() or 0
        
        # Calcular profit/loss
        total_profit = float(total_won) - float(total_staked)
        
        # Win rate
        settled_bets = won_bets + lost_bets + void_bets
        win_rate = (won_bets / settled_bets * 100) if settled_bets > 0 else 0
        
        # ROI
        roi = (total_profit / float(total_staked) * 100) if total_staked > 0 else 0
        
        return {
            "total_bets": total_bets,
            "won_bets": won_bets,
            "lost_bets": lost_bets,
            "void_bets": void_bets,
            "pending_bets": pending_bets,
            "total_staked": float(total_staked),
            "total_won": float(total_won),
            "total_profit": total_profit,
            "win_rate": win_rate,
            "roi": roi
        }