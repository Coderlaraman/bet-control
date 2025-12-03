from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class SportStatisticsResponse(BaseModel):
    """Schema de respuesta para estadísticas por deporte"""
    id: int
    user_id: int
    sport_id: int
    total_bets: int
    won_bets: int
    lost_bets: int
    void_bets: int
    total_staked: Decimal
    total_profit: Decimal
    win_rate: Optional[Decimal]
    roi: Optional[Decimal]
    average_odds: Optional[Decimal]
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class LeagueStatisticsResponse(BaseModel):
    """Schema de respuesta para estadísticas por liga"""
    id: int
    user_id: int
    league_id: int
    total_bets: int
    won_bets: int
    lost_bets: int
    void_bets: int
    total_staked: Decimal
    total_profit: Decimal
    win_rate: Optional[Decimal]
    roi: Optional[Decimal]
    average_odds: Optional[Decimal]
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class BettingPerformance(BaseModel):
    """Schema para rendimiento general de apuestas"""
    total_bets: int
    won_bets: int
    lost_bets: int
    void_bets: int
    pending_bets: int
    total_staked: Decimal
    total_profit: Decimal
    total_return: Decimal
    win_rate: float
    roi: float
    average_odds: float
    profit_factor: float
    expected_value: float


class SportPerformance(BaseModel):
    """Schema para rendimiento por deporte"""
    sport_name: str
    total_bets: int
    won_bets: int
    lost_bets: int
    void_bets: int
    total_staked: Decimal
    total_profit: Decimal
    win_rate: float
    roi: float
    average_odds: float


class LeaguePerformance(BaseModel):
    """Schema para rendimiento por liga"""
    league_name: str
    sport_name: str
    total_bets: int
    won_bets: int
    lost_bets: int
    void_bets: int
    total_staked: Decimal
    total_profit: Decimal
    win_rate: float
    roi: float
    average_odds: float


class MonthlyPerformance(BaseModel):
    """Schema para rendimiento mensual"""
    month: str
    year: int
    total_bets: int
    won_bets: int
    lost_bets: int
    void_bets: int
    total_staked: Decimal
    total_profit: Decimal
    win_rate: float
    roi: float