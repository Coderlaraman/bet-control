from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from app.models.bet import BetStatus


class BetBase(BaseModel):
    """Base schema para apuestas"""
    sport_id: int
    country_id: Optional[int] = None
    league_id: Optional[int] = None
    market_id: Optional[int] = None
    event_name: str = Field(..., min_length=3, max_length=200)
    event_date: datetime
    event_time: Optional[datetime] = None
    home_team: Optional[str] = Field(None, max_length=100)
    away_team: Optional[str] = Field(None, max_length=100)
    bet_description: str = Field(..., min_length=1, max_length=500)
    odds: Decimal = Field(..., gt=1.0)
    stake: Decimal = Field(..., gt=0)
    bet_type_id: int
    notes: Optional[str] = Field(None, max_length=1000)


class BetCreate(BetBase):
    """Schema para crear apuesta"""
    pass


class BetUpdate(BaseModel):
    """Schema para actualizar apuesta"""
    sport_id: Optional[int] = None
    country_id: Optional[int] = None
    league_id: Optional[int] = None
    market_id: Optional[int] = None
    event_name: Optional[str] = Field(None, min_length=3, max_length=200)
    event_date: Optional[datetime] = None
    event_time: Optional[datetime] = None
    home_team: Optional[str] = Field(None, max_length=100)
    away_team: Optional[str] = Field(None, max_length=100)
    bet_description: Optional[str] = Field(None, min_length=1, max_length=500)
    odds: Optional[Decimal] = Field(None, gt=1.0)
    stake: Optional[Decimal] = Field(None, gt=0)
    bet_type_id: Optional[int] = None
    status: Optional[BetStatus] = None
    result_amount: Optional[Decimal] = None
    notes: Optional[str] = Field(None, max_length=1000)


class BetResponse(BetBase):
    """Schema de respuesta para apuesta"""
    id: int
    user_id: int
    status: BetStatus
    potential_win: Decimal
    result_amount: Optional[Decimal]
    settled_at: Optional[datetime]
    bet_slip_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ParlaySelectionBase(BaseModel):
    """Base schema para selección de parlay"""
    sport_id: int
    league_id: Optional[int] = None
    event_name: str = Field(..., min_length=3, max_length=200)
    event_date: datetime
    market_id: Optional[int] = None
    selection: str = Field(..., min_length=1, max_length=200)
    odds: Decimal = Field(..., gt=1.0)


class ParlaySelectionCreate(ParlaySelectionBase):
    """Schema para crear selección de parlay"""
    pass


class ParlaySelectionResponse(ParlaySelectionBase):
    """Schema de respuesta para selección de parlay"""
    id: int
    parlay_id: int
    status: Optional[str]
    
    class Config:
        from_attributes = True


class ParlayBetBase(BaseModel):
    """Base schema para apuesta combinada"""
    bet_type_id: int
    total_stake: Decimal = Field(..., gt=0)
    selections: List[ParlaySelectionCreate]


class ParlayBetCreate(ParlayBetBase):
    """Schema para crear apuesta combinada"""
    pass


class ParlayBetResponse(BaseModel):
    """Schema de respuesta para apuesta combinada"""
    id: int
    user_id: int
    bet_type_id: int
    total_odds: Decimal
    total_stake: Decimal
    potential_win: Decimal
    status: str
    result_amount: Optional[Decimal]
    settled_at: Optional[datetime]
    created_at: datetime
    selections: List[ParlaySelectionResponse]
    
    class Config:
        from_attributes = True


class BetStatistics(BaseModel):
    """Schema para estadísticas de apuestas"""
    total_bets: int
    won_bets: int
    lost_bets: int
    void_bets: int
    pending_bets: int
    total_staked: Decimal
    total_profit: Decimal
    win_rate: float
    roi: float
    average_odds: float


class BetFilter(BaseModel):
    """Schema para filtros de búsqueda de apuestas"""
    sport_id: Optional[int] = None
    country_id: Optional[int] = None
    league_id: Optional[int] = None
    market_id: Optional[int] = None
    status: Optional[BetStatus] = None
    bet_type_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_odds: Optional[Decimal] = None
    max_odds: Optional[Decimal] = None
    min_stake: Optional[Decimal] = None
    max_stake: Optional[Decimal] = None