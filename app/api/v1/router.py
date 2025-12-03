from fastapi import APIRouter

from app.api.v1.endpoints import auth, bets, bankroll, ai

api_router = APIRouter()

# Incluir todos los routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(bets.router, prefix="/bets", tags=["bets"])
api_router.include_router(bankroll.router, prefix="/bankroll", tags=["bankroll"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])