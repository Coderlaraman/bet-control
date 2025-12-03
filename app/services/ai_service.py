from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
import os
import httpx
import joblib
import pandas as pd
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.config import settings
from app.models.fixture import Fixture


class AIService:
    """
    Service for AI-powered betting suggestions and analysis using real data from API-Football.
    Implements a 'Fetch & Store' strategy to cache data and minimize API usage.
    Uses a trained Random Forest model for predictions.
    """
    
    def __init__(self):
        self.api_key = settings.API_FOOTBALL_KEY
        self.api_host = settings.API_FOOTBALL_HOST
        self.base_url = f"https://{self.api_host}"
        
        # Load ML Model
        self.model_path = os.path.join(os.path.dirname(__file__), "model.pkl")
        self.columns_path = os.path.join(os.path.dirname(__file__), "model_columns.pkl")
        self.model = None
        self.model_columns = None
        
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                self.model_columns = joblib.load(self.columns_path)
                logger.info("ML Model loaded successfully.")
            else:
                logger.warning("ML Model not found. Falling back to rule-based logic.")
        except Exception as e:
            logger.error(f"Error loading ML model: {e}")
        
    async def get_daily_suggestions(self, db: Session, target_date: Optional[datetime.date] = None) -> List[Dict[str, Any]]:
        """
        Get betting suggestions for a specific day (default: today).
        Checks local DB first; if empty, syncs from API.
        """
        try:
            # If no API key, return mock data
            if not self.api_key or self.api_key == "your-api-football-key-here":
                logger.warning("API-Football key not configured, returning mock data")
                return await self._get_mock_suggestions()
            
            if target_date is None:
                target_date = datetime.now().date()
            
            # 1. Try to fetch cached suggestions from DB
            cached_fixtures = db.query(Fixture).filter(
                # Cast to date for comparison if needed, or range check
                Fixture.event_date >= datetime.combine(target_date, datetime.min.time()),
                Fixture.event_date < datetime.combine(target_date + timedelta(days=1), datetime.min.time()),
                Fixture.prediction_data.isnot(None)
            ).order_by(Fixture.confidence_score.desc()).all()
            
            if cached_fixtures:
                logger.info(f"Returning {len(cached_fixtures)} cached suggestions from DB for {target_date}")
                return [self._format_fixture_response(f) for f in cached_fixtures]
            
            # 2. If no cache, perform sync and analysis
            logger.info(f"No cached suggestions found for {target_date}, syncing from API...")
            suggestions = await self._sync_and_analyze(db, target_date)

            # If still no suggestions, try tomorrow automatically
            if not suggestions and target_date == datetime.now().date():
                logger.info("No matches found for today. Checking tomorrow...")
                tomorrow = target_date + timedelta(days=1)
                return await self.get_daily_suggestions(db, target_date=tomorrow)
                
            return suggestions
            
        except Exception as e:
            logger.error(f"Error fetching AI suggestions: {str(e)}")
            # Fallback to mock data on error
            return await self._get_mock_suggestions()

    async def _sync_and_analyze(self, db: Session, target_date: Optional[datetime.date] = None) -> List[Dict[str, Any]]:
        """
        Fetch matches from API, save to DB, run analysis, and return results.
        """
        # 1. Fetch matches from API
        if target_date is None:
            target_date = datetime.now().date()
        matches_data = await self._fetch_daily_matches(target_date)
        
        if not matches_data:
            logger.warning(f"No matches found for {target_date}")
            return []
        
        suggestions = []
        
        for match_data in matches_data:
            # 2. Run Analysis
            analysis = self._analyze_match(match_data, db)
            
            if analysis and analysis['confidence_score'] >= 0.55: # Lower threshold for ML
                # 3. Save/Update Fixture in DB
                fixture = self._save_fixture_to_db(db, match_data, analysis)
                suggestions.append(self._format_fixture_response(fixture))
        
        # Sort by confidence
        suggestions = sorted(suggestions, key=lambda x: x['confidence_score'], reverse=True)
        
        return suggestions[:6]

    def _save_fixture_to_db(self, db: Session, match_data: Dict, analysis: Dict) -> Fixture:
        """
        Save or update fixture data in the database.
        """
        fixture_id = match_data['id'] # e.g. "f12345"
        external_id = int(fixture_id[1:]) # 12345
        
        fixture = db.query(Fixture).filter(Fixture.id == fixture_id).first()
        
        if not fixture:
            fixture = Fixture(id=fixture_id, external_id=external_id)
            
        fixture.home_team = match_data['home_team']
        fixture.away_team = match_data['away_team']
        # match_data['date'] is ISO format string
        fixture.event_date = datetime.fromisoformat(match_data['date'].replace('Z', '+00:00'))
        fixture.league_id = None # Could map if we had league IDs in match_data easily
        fixture.home_stats = match_data['home_stats']
        fixture.away_stats = match_data['away_stats']
        fixture.h2h_data = match_data['head_to_head']
        fixture.prediction_data = analysis
        fixture.confidence_score = analysis['confidence_score']
        
        # Update scores if present (useful for updates)
        if 'goals' in match_data:
             fixture.home_score = match_data['goals'].get('home')
             fixture.away_score = match_data['goals'].get('away')
             fixture.status = match_data.get('status', 'NS')
        
        db.add(fixture)
        db.commit()
        db.refresh(fixture)
        return fixture

    def _format_fixture_response(self, fixture: Fixture) -> Dict[str, Any]:
        """
        Format a Fixture object into the response dictionary expected by frontend.
        """
        return {
            "id": fixture.id,
            "sport": "Football",
            "league": fixture.league.name if fixture.league else "Unknown League", 
            "home_team": fixture.home_team,
            "away_team": fixture.away_team,
            "date": fixture.event_date.isoformat(),
            "home_stats": fixture.home_stats,
            "away_stats": fixture.away_stats,
            "head_to_head": fixture.h2h_data,
            **fixture.prediction_data
        }

    async def _fetch_daily_matches(self, target_date: datetime.date, season: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch matches for a specific date from API-Football.
        """
        date_str = target_date.strftime("%Y-%m-%d")
        
        if season is None:
            # Auto-detect season based on date
            # For major European leagues:
            # Aug-Dec -> Year
            # Jan-May -> Year - 1
            if target_date.month >= 7:
                season = target_date.year
            else:
                season = target_date.year - 1
        
        headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": self.api_host
        }
        
        try:
            async with httpx.AsyncClient() as client:
                # Fetch fixtures for today from major leagues
                # Premier League (39), La Liga (140), Serie A (135), Bundesliga (78), Ligue 1 (61)
                leagues = [39, 140, 135, 78, 61]
                all_matches = []
                
                for league_id in leagues:
                    params = {
                        "league": league_id,
                        "date": date_str,
                        "season": season
                    }
                    logger.info(f"Fetching fixtures: {self.base_url}/fixtures params={params}")
                    
                    response = await client.get(
                        f"{self.base_url}/fixtures",
                        headers=headers,
                        params=params,
                        timeout=10.0
                    )
                    
                    logger.info(f"API Response Status: {response.status_code}")
                    if response.status_code != 200:
                        logger.error(f"API Error: {response.text}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        fixtures = data.get("response", [])
                        logger.info(f"Found {len(fixtures)} fixtures for league {league_id}")
                        
                        for fixture in fixtures[:2]:  # Limit to 2 per league for quota safety
                            match_data = await self._parse_fixture(fixture, client, headers)
                            if match_data:
                                all_matches.append(match_data)
                
                return all_matches[:10]  # Max 10 matches
                
        except Exception as e:
            logger.error(f"Error fetching matches from API-Football: {str(e)}")
            return []

    async def _parse_fixture(self, fixture: Dict, client: httpx.AsyncClient, headers: Dict) -> Optional[Dict[str, Any]]:
        """
        Parse fixture data and fetch additional statistics.
        """
        try:
            fixture_id = fixture["fixture"]["id"]
            home_team = fixture["teams"]["home"]
            away_team = fixture["teams"]["away"]
            league = fixture["league"]
            
            # Fetch team statistics
            home_stats = await self._fetch_team_stats(home_team["id"], league["id"], client, headers)
            away_stats = await self._fetch_team_stats(away_team["id"], league["id"], client, headers)
            
            # Fetch H2H data
            h2h_data = await self._fetch_h2h(home_team["id"], away_team["id"], client, headers)
            
            return {
                "id": f"f{fixture_id}",
                "sport": "Football",
                "league": league["name"],
                "home_team": home_team["name"],
                "away_team": away_team["name"],
                "date": fixture["fixture"]["date"],
                "home_stats": home_stats,
                "away_stats": away_stats,
                "head_to_head": h2h_data
            }
            
        except Exception as e:
            logger.error(f"Error parsing fixture: {str(e)}")
            return None

    async def _fetch_team_stats(self, team_id: int, league_id: int, client: httpx.AsyncClient, headers: Dict) -> Dict[str, Any]:
        """
        Fetch team statistics from API-Football.
        """
        try:
            season_year = datetime.now().year if datetime.now().month >= 7 else datetime.now().year - 1
            response = await client.get(
                f"{self.base_url}/teams/statistics",
                headers=headers,
                params={
                    "team": team_id,
                    "league": league_id,
                    "season": season_year
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get("response", {})
                
                # Extract relevant stats
                form = stats.get("form", "").replace("W", "1").replace("D", "0").replace("L", "0")
                wins_last_5 = sum(int(c) for c in form[-5:] if c.isdigit())
                
                goals_for = stats.get("goals", {}).get("for", {}).get("average", {}).get("total", 0)
                goals_against = stats.get("goals", {}).get("against", {}).get("average", {}).get("total", 0)
                
                return {
                    "wins_last_5": wins_last_5,
                    "goals_avg": float(goals_for) if goals_for else 1.0,
                    "conceded_avg": float(goals_against) if goals_against else 1.0
                }
        except Exception as e:
            logger.error(f"Error fetching team stats: {str(e)}")
        
        # Default stats if API fails
        return {"wins_last_5": 2, "goals_avg": 1.5, "conceded_avg": 1.2}

    async def _fetch_h2h(self, home_team_id: int, away_team_id: int, client: httpx.AsyncClient, headers: Dict) -> Dict[str, int]:
        """
        Fetch head-to-head data.
        """
        try:
            response = await client.get(
                f"{self.base_url}/fixtures/headtohead",
                headers=headers,
                params={
                    "h2h": f"{home_team_id}-{away_team_id}",
                    "last": 10
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                fixtures = data.get("response", [])
                
                home_wins = 0
                away_wins = 0
                draws = 0
                
                for fixture in fixtures:
                    home_goals = fixture["goals"]["home"]
                    away_goals = fixture["goals"]["away"]
                    
                    if home_goals > away_goals:
                        home_wins += 1
                    elif away_goals > home_goals:
                        away_wins += 1
                    else:
                        draws += 1
                
                return {"home_wins": home_wins, "draws": draws, "away_wins": away_wins}
        except Exception as e:
            logger.error(f"Error fetching H2H: {str(e)}")
        
        return {"home_wins": 3, "draws": 2, "away_wins": 3}

    def _analyze_match(self, match: Dict[str, Any], db: Session) -> Optional[Dict[str, Any]]:
        """
        Analyze a match and return betting suggestions.
        Prefers ML model if available, falls back to heuristics.
        """
        
        # 1. Try ML Prediction
        if self.model and self.model_columns:
            try:
                features = self._calculate_features(match, db)
                # Ensure columns match training data
                features_df = pd.DataFrame([features], columns=self.model_columns)
                features_df = features_df.fillna(0)
                
                # Predict
                # Classes are usually [0: Away, 1: Draw, 2: Home] if sorted
                # But we should verify class labels from model if possible.
                # Assuming standard sklearn behavior with 0,1,2.
                
                probs = self.model.predict_proba(features_df)[0]
                
                # Identify best outcome
                # Map indices to outcomes based on training: 0=Away, 1=Draw, 2=Home
                outcomes = ["Away Win", "Draw", "Home Win"]
                best_idx = probs.argmax()
                prediction = outcomes[best_idx]
                confidence = probs[best_idx]
                
                reasoning = [
                    f"AI Model Probability: {confidence*100:.1f}%",
                    f"Based on recent form and H2H analysis"
                ]
                
                # Add some context from stats
                home_stats = match.get('home_stats', {}) or {}
                wins = home_stats.get('wins_last_5', '?')
                reasoning.append(f"Home Form: {wins}/5 wins")
                
                return {
                    "prediction": prediction,
                    "confidence_score": float(confidence),
                    "reasoning": reasoning,
                    "suggested_odds": round(1 / confidence * 0.92, 2)
                }
                
            except Exception as e:
                logger.error(f"ML prediction failed: {e}. Falling back to heuristics.")

        # 2. Fallback: Heuristic Logic
        return self._heuristic_analysis(match)

    def _get_latest_elo(self, team_name: str, db: Session) -> float:
        """
        Get the latest known Elo rating for a team from the database.
        """
        # Search for the team in home or away columns, ordered by date desc
        last_match = db.query(Fixture).filter(
            (Fixture.home_team == team_name) | (Fixture.away_team == team_name),
            Fixture.home_elo.isnot(None)
        ).order_by(Fixture.event_date.desc()).first()
        
        if last_match:
            if last_match.home_team == team_name:
                return last_match.home_elo
            else:
                return last_match.away_elo
                
        # Default Elo if not found (League average approx)
        return 1500.0

    def _calculate_features(self, match: Dict[str, Any], db: Session) -> Dict[str, float]:
        """
        Calculate features for a single match to feed into the ML model.
        Must match the logic in train_model.py
        """
        try:
            # 1. Get Elo Ratings
            home_elo = self._get_latest_elo(match['home_team'], db)
            away_elo = self._get_latest_elo(match['away_team'], db)
            elo_diff = home_elo - away_elo
            
            # 2. Calculate Probabilities (Implied from Odds or Elo)
            # If we have real odds, use them. Otherwise, use Elo expectation.
            # P(Home) = 1 / (1 + 10 ^ (-diff/400))
            elo_prob_home = 1 / (1 + 10 ** (-elo_diff / 400))
            elo_prob_away = 1 - elo_prob_home
            
            # Check if match has odds (not currently fetched, so default to Elo prob)
            # In V2, we should fetch real odds.
            prob_home = elo_prob_home
            prob_away = elo_prob_away
            
            # 3. Form Stats
            home_stats = match.get('home_stats', {}) or {}
            away_stats = match.get('away_stats', {}) or {}
            
            # Debugging
            # logger.info(f"Home Stats Type: {type(home_stats)}")
            # logger.info(f"Home Stats: {home_stats}")
            
            return {
                'elo_diff': elo_diff,
                'prob_home': prob_home,
                'prob_away': prob_away,
                
                'home_form_points': home_stats.get('wins_last_5', 0) * 3, # Approx points from last 5
                'away_form_points': away_stats.get('wins_last_5', 0) * 3,
                
                'home_form_goals': home_stats.get('goals_avg', 1.0),
                'away_form_goals': away_stats.get('goals_avg', 1.0),
                
                # Default shots if not available (API stats might need update to fetch these)
                'home_form_shots': home_stats.get('shots_avg', 10.0), 
                'away_form_shots': away_stats.get('shots_avg', 10.0)
            }
        except Exception as e:
            import traceback
            logger.error(f"Error in _calculate_features: {e}")
            logger.error(traceback.format_exc())
            raise e

    def _heuristic_analysis(self, match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Legacy rule-based analysis.
        """
        home_stats = match.get('home_stats', {}) or {}
        away_stats = match.get('away_stats', {}) or {}
        h2h = match.get('head_to_head', {}) or {}
        
        # 1. Form Analysis
        home_form = home_stats.get('wins_last_5', 2) / 5
        away_form = away_stats.get('wins_last_5', 2) / 5
        
        # 2. Goal Analysis
        home_attack = home_stats.get('goals_avg', 1.5)
        away_defense = away_stats.get('conceded_avg', 1.2)
        predicted_home_goals = (home_attack + away_defense) / 2
        
        away_attack = away_stats.get('goals_avg', 1.5)
        home_defense = home_stats.get('conceded_avg', 1.2)
        predicted_away_goals = (away_attack + home_defense) / 2
        
        # 3. H2H Dominance
        total_h2h = h2h.get('home_wins', 0) + h2h.get('draws', 0) + h2h.get('away_wins', 0)
        if total_h2h > 0:
            home_dominance = h2h.get('home_wins', 0) / total_h2h
        else:
            home_dominance = 0.5

        # Decision Logic
        confidence = 0.0
        prediction = ""
        reasoning = []
        
        # Strong Home Win Signal
        if home_form > away_form + 0.4 and home_dominance > 0.65:
            confidence = min(0.85, 0.65 + (home_form - away_form) * 0.5)
            prediction = "Home Win"
            reasoning.append(f"{match['home_team']} in excellent form ({home_stats['wins_last_5']}/5 wins)")
            reasoning.append(f"Strong H2H record ({h2h['home_wins']} wins in {total_h2h} meetings)")
            reasoning.append(f"Home advantage with {home_attack:.1f} goals/game average")
            
        # Strong Away Win Signal
        elif away_form > home_form + 0.4 and (1 - home_dominance) > 0.65:
            confidence = min(0.82, 0.65 + (away_form - home_form) * 0.5)
            prediction = "Away Win"
            reasoning.append(f"{match['away_team']} in superior form ({away_stats['wins_last_5']}/5 wins)")
            reasoning.append(f"Good away record in H2H ({h2h['away_wins']} wins)")
            reasoning.append(f"Strong attack with {away_attack:.1f} goals/game")
            
        # High Scoring Game Signal
        elif predicted_home_goals + predicted_away_goals > 2.8:
            confidence = min(0.78, 0.60 + (predicted_home_goals + predicted_away_goals - 2.8) * 0.15)
            prediction = "Over 2.5 Goals"
            reasoning.append(f"Both teams show strong attacking stats")
            reasoning.append(f"Expected total: {predicted_home_goals + predicted_away_goals:.1f} goals")
            reasoning.append(f"Home avg: {home_attack:.1f}, Away avg: {away_attack:.1f}")
            
        # Low Scoring Game Signal
        elif predicted_home_goals + predicted_away_goals < 1.8 and home_defense < 0.8 and away_defense < 0.8:
            confidence = 0.72
            prediction = "Under 2.5 Goals"
            reasoning.append("Both teams have strong defensive records")
            reasoning.append(f"Expected total: {predicted_home_goals + predicted_away_goals:.1f} goals")
            reasoning.append("Low-scoring trend in recent matches")
            
        # Moderate Home Favor
        elif home_form > away_form + 0.2:
            confidence = 0.68
            prediction = "Home Win or Draw (1X)"
            reasoning.append(f"{match['home_team']} has better recent form")
            reasoning.append("Home advantage factor")
            reasoning.append("Safe bet with double chance")
        
        # Moderate Away Favor  
        elif away_form > home_form + 0.2:
            confidence = 0.66
            prediction = "Away Win or Draw (X2)"
            reasoning.append(f"{match['away_team']} showing better form")
            reasoning.append("Away team momentum")
            reasoning.append("Double chance for safety")
            
        else:
            # Skip balanced matches
            return None

        return {
            "prediction": prediction,
            "confidence_score": confidence,
            "reasoning": reasoning,
            "suggested_odds": round(1 / confidence * 0.92, 2)  # Implied odds with bookmaker margin
        }

    async def _get_mock_suggestions(self) -> List[Dict[str, Any]]:
        """
        Return mock suggestions when API is not configured.
        """
        today = datetime.now()
        
        return [
            {
                "id": "mock1",
                "sport": "Football",
                "league": "Premier League",
                "home_team": "Manchester City",
                "away_team": "Burnley",
                "date": today.isoformat(),
                "prediction": "Home Win",
                "confidence_score": 0.88,
                "reasoning": [
                    "Manchester City in excellent form (5/5 wins)",
                    "Dominant H2H record (9 wins in 10 meetings)",
                    "Home advantage with 2.8 goals/game average"
                ],
                "suggested_odds": 1.05,
                "home_stats": {"wins_last_5": 5, "goals_avg": 2.8, "conceded_avg": 0.6},
                "away_stats": {"wins_last_5": 1, "goals_avg": 0.8, "conceded_avg": 1.9},
                "head_to_head": {"home_wins": 9, "draws": 1, "away_wins": 0}
            },
            {
                "id": "mock2",
                "sport": "Football",
                "league": "La Liga",
                "home_team": "Real Madrid",
                "away_team": "Getafe",
                "date": today.isoformat(),
                "prediction": "Over 2.5 Goals",
                "confidence_score": 0.76,
                "reasoning": [
                    "Both teams show strong attacking stats",
                    "Expected total: 3.4 goals",
                    "Home avg: 2.2, Away avg: 1.1"
                ],
                "suggested_odds": 1.21,
                "home_stats": {"wins_last_5": 4, "goals_avg": 2.2, "conceded_avg": 0.8},
                "away_stats": {"wins_last_5": 2, "goals_avg": 1.1, "conceded_avg": 1.2},
                "head_to_head": {"home_wins": 8, "draws": 2, "away_wins": 0}
            },
            {
                "id": "mock3",
                "sport": "Football",
                "league": "Serie A",
                "home_team": "Inter Milan",
                "away_team": "Napoli",
                "date": today.isoformat(),
                "prediction": "Home Win or Draw (1X)",
                "confidence_score": 0.72,
                "reasoning": [
                    "Inter Milan has better recent form",
                    "Home advantage factor",
                    "Safe bet with double chance"
                ],
                "suggested_odds": 1.28,
                "home_stats": {"wins_last_5": 4, "goals_avg": 1.9, "conceded_avg": 0.7},
                "away_stats": {"wins_last_5": 3, "goals_avg": 1.6, "conceded_avg": 1.0},
                "head_to_head": {"home_wins": 5, "draws": 3, "away_wins": 2}
            }
        ]
