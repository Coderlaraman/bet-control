import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger
from app.core.config import settings

class DavidGoliathService:
    """
    Specialized AI Service to detect 'David vs Goliath' mismatch opportunities.
    Focuses on League Standings and Structural inequalities.
    """
    
    def __init__(self):
        self.api_key = settings.API_FOOTBALL_KEY
        self.api_host = settings.API_FOOTBALL_HOST
        self.base_url = f"https://{self.api_host}"
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": self.api_host
        }
        # Cache standings in memory for the session (or short term)
        # Format: {league_id: {season: [standings_data]}}
        self._standings_cache = {}

    async def get_opportunities(self) -> List[Dict[str, Any]]:
        """
        Scan major leagues for upcoming David vs Goliath matches.
        """
        opportunities = []
        if not self.api_key:
            logger.warning("API-Football key not configured")
            return opportunities
        
        # Major Leagues IDs (Premier, La Liga, Serie A, Bundesliga, Ligue 1)
        leagues = [39, 140, 135, 78, 61] 
        
        async with httpx.AsyncClient() as client:
            for league_id in leagues:
                # 1. Get Standings
                standings = await self._get_standings(client, league_id)
                if not standings:
                    continue
                    
                # Map Team ID to Rank/Data for quick lookup
                team_ranks = {
                    team['team']['id']: {
                        'rank': team['rank'],
                        'points': team['points'],
                        'form': team['form'],
                        'name': team['team']['name']
                    } 
                    for team in standings
                }
                
                # 2. Get Upcoming Matches (Next 3 days)
                matches = await self._get_upcoming_matches(client, league_id)
                
                # 3. Analyze Mismatches
                for match in matches:
                    home_id = match['teams']['home']['id']
                    away_id = match['teams']['away']['id']
                    
                    if home_id not in team_ranks or away_id not in team_ranks:
                        continue
                        
                    home_data = team_ranks[home_id]
                    away_data = team_ranks[away_id]
                    
                    analysis = self._detect_mismatch(home_data, away_data)
                    
                    if analysis:
                        opportunities.append({
                            "match_id": match['fixture']['id'],
                            "date": match['fixture']['date'],
                            "league": match['league']['name'],
                            "home_team": home_data['name'],
                            "away_team": away_data['name'],
                            "type": "David vs Goliath",
                            "analysis": analysis,
                            "confidence": analysis['confidence']
                        })
        
        # Sort by confidence
        opportunities.sort(key=lambda x: x['confidence'], reverse=True)
        return opportunities

    async def _get_standings(self, client: httpx.AsyncClient, league_id: int) -> List[Dict]:
        """
        Fetch league standings. Uses cache if available.
        """
        current_year = datetime.now().year
        # Season logic: If month < 7, use previous year (e.g., in Feb 2025, season is 2024)
        season = current_year if datetime.now().month >= 7 else current_year - 1
        
        cache_key = f"{league_id}_{season}"
        if cache_key in self._standings_cache:
            return self._standings_cache[cache_key]
            
        try:
            response = await client.get(
                f"{self.base_url}/standings",
                headers=self.headers,
                params={"league": league_id, "season": season},
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                if data['response']:
                    # API Football returns standings as a list of lists (groups). 
                    # For major leagues, it's usually response[0]['league']['standings'][0]
                    standings = data['response'][0]['league']['standings'][0]
                    self._standings_cache[cache_key] = standings
                    return standings
        except Exception as e:
            logger.error(f"Error fetching standings for league {league_id}: {e}")
            return []
        return []

    async def _get_upcoming_matches(self, client: httpx.AsyncClient, league_id: int) -> List[Dict]:
        """
        Fetch fixtures for the next few days.
        """
        today = datetime.now().date()
        # Fetch logic is simplified for "next 10 matches" to catch upcoming round
        try:
            response = await client.get(
                f"{self.base_url}/fixtures",
                headers=self.headers,
                params={
                    "league": league_id,
                    "season": datetime.now().year if datetime.now().month >= 7 else datetime.now().year - 1,
                    "next": 10
                },
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json().get('response', [])
        except Exception as e:
            logger.error(f"Error fetching matches: {e}")
        return []

    def _detect_mismatch(self, home: Dict, away: Dict) -> Optional[Dict]:
        """
        Core Logic: Identify if there is a significant imbalance.
        """
        rank_diff = away['rank'] - home['rank'] # Positive if Home is higher rank (lower number)
        
        # Scenario 1: Goliath at Home (Top 5 vs Bottom 5)
        if home['rank'] <= 5 and away['rank'] >= 15:
            return {
                "goliath": home['name'],
                "david": away['name'],
                "scenario": "Titan at Home",
                "details": f"{home['name']} (Rank {home['rank']}) vs {away['name']} (Rank {away['rank']})",
                "confidence": 0.85,
                "recommendation": f"Back {home['name']} to win"
            }
            
        # Scenario 2: Goliath Away (Top 3 vs Bottom 3)
        # Away games are riskier, so we demand higher rank diff
        if away['rank'] <= 3 and home['rank'] >= 18:
             return {
                "goliath": away['name'],
                "david": home['name'],
                "scenario": "Titan Away",
                "details": f"{away['name']} (Rank {away['rank']}) visits {home['name']} (Rank {home['rank']})",
                "confidence": 0.75,
                "recommendation": f"Back {away['name']} to win"
            }
            
        # Scenario 3: David in Crisis (Mid-table vs Bottom in terrible form)
        # This would require parsing 'form' string "LLLDL"
        
        return None
