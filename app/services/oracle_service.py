import datetime
from typing import Dict, Any, Optional, List
from loguru import logger
from sqlalchemy.orm import Session
from app.services.smart_bet_entry import SmartBetEntryService
from app.services.ai_service import AIService
from app.models.fixture import Fixture

class OracleService:
    """
    'The Oracle': Interactive AI Assistant for validating bet ideas.
    Combines NLP intent recognition with Match Analysis logic.
    """

    def __init__(self, db: Session):
        self.db = db
        self.nlp_service = SmartBetEntryService()
        self.ai_service = AIService()

    async def ask_oracle(self, query: str) -> Dict[str, Any]:
        """
        Process a natural language query about a bet/match and return an AI verdict.
        """
        # 1. Parse the query to find teams/intent
        intent = self.nlp_service.parse_bet_description(query)
        
        target_team = intent.get("selection") or intent.get("home_team") or intent.get("away_team")
        
        if not target_team:
            return {
                "status": "unknown",
                "message": "I couldn't identify a team in your question. Please try naming a specific team like 'Real Madrid' or 'Arsenal'."
            }

        # 2. Find the relevant match (Upcoming)
        # Search in DB for upcoming matches involving this team
        # We look for matches in the next 7 days
        today = datetime.datetime.now().date()
        next_week = today + datetime.timedelta(days=7)
        
        match = self.db.query(Fixture).filter(
            (Fixture.home_team.ilike(f"%{target_team}%")) | (Fixture.away_team.ilike(f"%{target_team}%")),
            Fixture.event_date >= today,
            Fixture.event_date <= next_week
        ).order_by(Fixture.event_date.asc()).first()
        
        if not match:
            # If not in DB, we might trigger a fetch, but for now let's say "No match found"
            # Or try to search via API (advanced)
            return {
                "status": "not_found",
                "message": f"I couldn't find an upcoming match for {target_team} in my database for the next 7 days."
            }

        # 3. Analyze the Match
        # Convert Fixture model to dict format expected by AI Service
        match_data = {
            "id": match.id,
            "home_team": match.home_team,
            "away_team": match.away_team,
            "date": match.event_date,
            "home_stats": match.home_stats or {},
            "away_stats": match.away_stats or {},
            "head_to_head": match.h2h_data or {},
            "home_elo": match.home_elo,
            "away_elo": match.away_elo
        }

        # Calculate Features & Prediction
        try:
            analysis = self.ai_service._analyze_match(match_data, self.db)
        except Exception as e:
            logger.error(f"Oracle analysis failed: {e}")
            analysis = None

        if not analysis:
            return {
                "status": "error",
                "message": "I found the match but couldn't generate a confident analysis right now."
            }

        # 4. Synthesize 'The Oracle' Verdict
        # We compare the user's intent (if they picked a winner) with our prediction
        
        user_pick = target_team # Simplification: assume they want to bet ON the team they mentioned
        
        # Determine AI pick
        ai_prediction = analysis['prediction'] # "Home Win", "Away Win", "Draw"
        confidence = analysis['confidence_score']
        
        is_agreement = False
        if "Home" in ai_prediction and match.home_team in user_pick:
            is_agreement = True
        elif "Away" in ai_prediction and match.away_team in user_pick:
            is_agreement = True
            
        # Construct Verdict
        verdict_color = "yellow"
        verdict_title = "Caution"
        
        if is_agreement and confidence > 0.60:
            verdict_color = "green"
            verdict_title = "Green Light"
            verdict_text = f"Yes! My model agrees. {match.home_team} vs {match.away_team} looks good for {user_pick}."
        elif not is_agreement and confidence > 0.60:
            verdict_color = "red"
            verdict_title = "Red Flag"
            verdict_text = f"Be careful. I actually favor {ai_prediction} (Confidence: {confidence:.0%}). Betting on {user_pick} might be risky."
        else:
            verdict_text = f"It's a toss-up. My model is uncertain ({confidence:.0%}). Proceed with caution."

        return {
            "status": "success",
            "match_info": f"{match.home_team} vs {match.away_team} ({match.event_date.strftime('%Y-%m-%d')})",
            "verdict": {
                "color": verdict_color,
                "title": verdict_title,
                "text": verdict_text,
                "confidence": confidence,
                "ai_prediction": ai_prediction,
                "reasoning": analysis['reasoning']
            }
        }
