from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import get_current_active_user
from app.api.deps import get_db
from app.models.user import User
from app.services.david_goliath_service import DavidGoliathService
from app.services.oracle_service import OracleService
from pydantic import BaseModel

router = APIRouter()

class OracleRequest(BaseModel):
    query: str

@router.post("/oracle/ask", status_code=status.HTTP_200_OK)
async def ask_the_oracle(
    request: OracleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Ask 'The Oracle' about a specific bet/match.
    """
    try:
        service = OracleService(db)
        response = await service.ask_oracle(request.query)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consulting the oracle: {str(e)}")

@router.get("/david-goliath", response_model=List[Any])
async def get_david_goliath_opportunities(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get specific 'David vs Goliath' betting opportunities based on structural league inequalities.
    """
    try:
        service = DavidGoliathService()
        opportunities = await service.get_opportunities()
        return opportunities
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing opportunities: {str(e)}")
