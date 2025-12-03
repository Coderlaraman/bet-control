from fastapi import APIRouter, Depends, HTTPException
from typing import List, Any
from sqlalchemy.orm import Session
from app.services.ai_service import AIService
from app.db.session import get_db

router = APIRouter()
ai_service = AIService()

@router.get("/suggestions", response_model=List[Any])
async def get_ai_suggestions(db: Session = Depends(get_db)):
    """
    Get AI-powered betting suggestions for today's matches.
    """
    try:
        suggestions = await ai_service.get_daily_suggestions(db)
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
