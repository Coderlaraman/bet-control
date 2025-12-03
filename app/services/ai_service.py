from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
import httpx
from loguru import logger
from app.core.config import settings


class AIService:
    """
    Service for AI-powered betting suggestions and analysis using real data from API-Football.
    """
    
    def __init__(self):
        self.api_key = settings.API_FOOTBALL_KEY
        self.api_host = settings.API_FOOTBALL_HOST
        self.base_url = f"https://{self.api_host}"
        
    async def get_daily_suggestions(self) -> List[Dict[str, Any]]:
        """
        Get betting suggestions for the current day using real API-Football data.
        """
        try:
            # If no API key, return mock data
            if not self.api_key or self.api_key == "your-api-football-key-here":
                logger.warning("API-Football key not configured, returning mock data")
                return await self._get_mock_suggestions()
            
            matches = await self._fetch_daily_matches()
            suggestions = []
            
            for match in matches:
                analysis = await self._analyze_match(match)
                if analysis and analysis['confidence_score'] >= 0.65:  # Only moderate+ confidence
                    suggestions.append({
                        **match,
                        **analysis
                    })
            
            # Sort by confidence
            suggestions = sorted(suggestions, key=lambda x: x['confidence_score'], reverse=True)
            
            # Return top 6 suggestions
            return suggestions[:6]
            
        except Exception as e:
            logger.error(f"Error fetching AI suggestions: {str(e)}")
            # Fallback to mock data on error
            return await self._get_mock_suggestions()

    async def _fetch_daily_matches(self) -> List[Dict[str, Any]]:
        """
        Fetch today's matches from API-Football.
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
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
                    response = await client.get(
                        f"{self.base_url}/fixtures",
                        headers=headers,
                        params={
                            "league": league_id,
                            "date": today,
                            "season": datetime.now().year
                        },
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        fixtures = data.get("response", [])
                        
                        for fixture in fixtures[:2]:  # Limit to 2 per league
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
            response = await client.get(
                f"{self.base_url}/teams/statistics",
                headers=headers,
                params={
                    "team": team_id,
                    "league": league_id,
                    "season": datetime.now().year
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

    async def _analyze_match(self, match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze a match and return betting suggestions if a clear advantage is found.
        """
        home_stats = match['home_stats']
        away_stats = match['away_stats']
        h2h = match['head_to_head']
        
        # 1. Form Analysis
        home_form = home_stats['wins_last_5'] / 5
        away_form = away_stats['wins_last_5'] / 5
        
        # 2. Goal Analysis
        home_attack = home_stats['goals_avg']
        away_defense = away_stats['conceded_avg']
        predicted_home_goals = (home_attack + away_defense) / 2
        
        away_attack = away_stats['goals_avg']
        home_defense = home_stats['conceded_avg']
        predicted_away_goals = (away_attack + home_defense) / 2
        
        # 3. H2H Dominance
        total_h2h = h2h['home_wins'] + h2h['draws'] + h2h['away_wins']
        if total_h2h > 0:
            home_dominance = h2h['home_wins'] / total_h2h
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
