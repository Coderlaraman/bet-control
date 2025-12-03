import asyncio
import os
import sys
from datetime import datetime, timedelta
import httpx
from loguru import logger
from sqlalchemy.orm import Session

# Add root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.fixture import Fixture
from app.core.config import settings

class BackfillService:
    def __init__(self):
        self.api_key = settings.API_FOOTBALL_KEY
        self.api_host = settings.API_FOOTBALL_HOST
        self.base_url = f"https://{self.api_host}"
        # Major leagues: PL (39), La Liga (140), Serie A (135), Bundesliga (78), Ligue 1 (61)
        self.target_leagues = [39, 140, 135, 78, 61]
        
    async def run_backfill(self, seasons: list[int] = [2024, 2025]):
        """
        Fetch past match results for the specified seasons.
        """
        logger.info(f"Starting backfill for seasons {seasons}...")
        db = SessionLocal()
        
        try:
            async with httpx.AsyncClient() as client:
                for season in seasons:
                    logger.info(f"Processing Season {season}...")
                    for league_id in self.target_leagues:
                        logger.info(f"Fetching matches for League {league_id} (Season {season})...")
                        await self._fetch_and_store_league_season(client, db, league_id, season)
                    
            logger.info("Backfill completed successfully.")
        except Exception as e:
            logger.error(f"Backfill failed: {e}")
        finally:
            db.close()

    async def _fetch_and_store_league_season(self, client: httpx.AsyncClient, db: Session, league_id: int, season: int):
        headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": self.api_host
        }
        
        try:
            # Fetch all finished matches for the league/season
            response = await client.get(
                f"{self.base_url}/fixtures",
                headers=headers,
                params={
                    "league": league_id,
                    "season": season,
                    "status": "FT" # Finished matches only
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                fixtures = data.get("response", [])
                logger.info(f"Found {len(fixtures)} matches for League {league_id}")
                
                count = 0
                for fixture_data in fixtures:
                    await self._store_fixture(db, fixture_data)
                    count += 1
                    if count % 50 == 0:
                        logger.info(f"Processed {count} matches...")
                        
            else:
                logger.error(f"API Error {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"Error processing league {league_id}: {e}")

    async def _store_fixture(self, db: Session, data: dict):
        """
        Store a single historical fixture.
        """
        try:
            fixture_id = f"f{data['fixture']['id']}"
            external_id = data['fixture']['id']
            
            # Check if exists
            existing = db.query(Fixture).filter(Fixture.id == fixture_id).first()
            if existing:
                return # Skip if already exists
            
            fixture = Fixture(
                id=fixture_id,
                external_id=external_id,
                home_team=data['teams']['home']['name'],
                away_team=data['teams']['away']['name'],
                event_date=datetime.fromisoformat(data['fixture']['date'].replace('Z', '+00:00')),
                status=data['fixture']['status']['short'],
                home_score=data['goals']['home'],
                away_score=data['goals']['away'],
                # For historical data, we might not have pre-match stats in this endpoint
                # We would need separate calls for that, which is expensive.
                # For now, we store the match result. 
                # To train a model, we ideally need PRE-MATCH stats.
                # API-Football 'fixtures' endpoint returns some stats if requested? 
                # No, stats are separate endpoint usually. 
                # But for 'result' prediction, we need the result.
                # We can try to fetch stats if available or leave null for now.
            )
            
            db.add(fixture)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error saving fixture {data.get('fixture', {}).get('id')}: {e}")
            db.rollback()

if __name__ == "__main__":
    service = BackfillService()
    # Free plan limitation: only 2021-2023 available
    asyncio.run(service.run_backfill(seasons=[2023]))
