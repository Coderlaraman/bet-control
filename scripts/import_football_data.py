import os
import sys
import pandas as pd
import io
import httpx
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from fuzzywuzzy import process
from loguru import logger

# Add root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.fixture import Fixture

# Configuration
SEASONS = ["2425", "2324"] # Download current and last season
BASE_URL = "https://www.football-data.co.uk/mmz4281"
LEAGUES = {
    "E0": "Premier League",
    "SP1": "La Liga",
    "I1": "Serie A",
    "D1": "Bundesliga",
    "F1": "Ligue 1"
}

# Known mapping issues (CSV Name -> Our DB Standard/API Name)
# We can expand this as we find mismatches
TEAM_MAPPING_OVERRIDES = {
    "Man United": "Manchester United",
    "Man City": "Manchester City",
    "Leicester": "Leicester City",
    "Leeds": "Leeds United",
    "Nott'm Forest": "Nottingham Forest",
    "Spurs": "Tottenham",
    "Ath Bilbao": "Athletic Club",
    "Ath Madrid": "Atletico Madrid",
    "Celta": "Celta Vigo",
    "Betis": "Real Betis",
    "Sociedad": "Real Sociedad",
    "Vallecano": "Rayo Vallecano",
    "Inter": "Inter Milan",
    "Milan": "AC Milan",
    "Leverkusen": "Bayer Leverkusen",
    "M'gladbach": "Borussia Monchengladbach",
    "Frankfurt": "Eintracht Frankfurt",
    "Mainz": "Mainz 05",
    "Dortmund": "Borussia Dortmund",
    "Paris SG": "Paris Saint Germain",
    "St Etienne": "Saint Etienne"
}

async def download_csv(league_code: str, season: str) -> pd.DataFrame:
    url = f"{BASE_URL}/{season}/{league_code}.csv"
    logger.info(f"Downloading {url}...")
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            # Decode with latin-1 usually used by football-data.co.uk
            content = response.content.decode('latin-1')
            return pd.read_csv(io.StringIO(content))
        else:
            logger.error(f"Failed to download {url}: {response.status_code}")
            return None

def normalize_team_name(name: str) -> str:
    if name in TEAM_MAPPING_OVERRIDES:
        return TEAM_MAPPING_OVERRIDES[name]
    return name.strip()

def safe_float(val):
    if pd.isna(val):
        return None
    return float(val)

def import_data():
    db = SessionLocal()
    try:
        for season in SEASONS:
            for code, league_name in LEAGUES.items():
                # Need to run async function in sync context or just use httpx sync?
                # Let's use sync for simplicity in this script
                try:
                    url = f"{BASE_URL}/{season}/{code}.csv"
                    logger.info(f"Processing {league_name} ({season})...")
                    
                    # Use pandas directly which handles remote CSVs
                    df = pd.read_csv(url, encoding='latin-1')
                    
                    count = 0
                    for _, row in df.iterrows():
                        if pd.isna(row['Date']):
                            continue
                            
                        try:
                            # Parse Date (dd/mm/yyyy)
                            date_str = row['Date']
                            # Handle 2-digit year if present
                            if len(date_str.split('/')[-1]) == 2:
                                date_fmt = "%d/%m/%y"
                            else:
                                date_fmt = "%d/%m/%Y"
                            
                            event_date = datetime.strptime(date_str, date_fmt)
                            
                            # Combine with Time if available
                            if 'Time' in row and not pd.isna(row['Time']):
                                time_str = row['Time']
                                # Basic check for HH:MM format
                                if ':' in str(time_str):
                                     hour, minute = map(int, str(time_str).split(':'))
                                     event_date = event_date.replace(hour=hour, minute=minute)

                            home_team = normalize_team_name(row['HomeTeam'])
                            away_team = normalize_team_name(row['AwayTeam'])
                            
                            # Generate a unique ID based on date and teams to avoid duplicates
                            # Format: f_YYYYMMDD_Home_Away (sanitized)
                            safe_home = "".join(c for c in home_team if c.isalnum())[:3]
                            safe_away = "".join(c for c in away_team if c.isalnum())[:3]
                            fixture_id = f"csv_{event_date.strftime('%Y%m%d')}_{safe_home}_{safe_away}"
                            
                            # Check if exists
                            existing = db.query(Fixture).filter(Fixture.id == fixture_id).first()
                            
                            # If not exists, check if we have it via API ID (fetched previously)
                            # This is harder to check without fuzzy matching everything.
                            # For now, we assume CSV data is "new" or "supplementary".
                            # To avoid duplicates with API data, we could check by date + teams.
                            
                            # Better check: Date + Teams
                            if not existing:
                                existing_match = db.query(Fixture).filter(
                                    Fixture.event_date >= event_date.replace(hour=0, minute=0, second=0),
                                    Fixture.event_date <= event_date.replace(hour=23, minute=59, second=59),
                                    Fixture.home_team == home_team
                                ).first()
                                
                                if existing_match:
                                    # Update existing match with stats/odds if needed
                                    # For now, just skip to avoid duplicates
                                    continue

                            fixture = Fixture(
                                id=fixture_id,
                                external_id=None, # No API ID
                                home_team=home_team,
                                away_team=away_team,
                                event_date=event_date,
                                status='FT', # CSVs only have finished matches usually
                                home_score=int(row['FTHG']),
                                away_score=int(row['FTAG']),
                                
                                # Store odds and stats in JSON fields
                                # Football-Data columns: HS (Home Shots), AS, HST (Target), AST, HC (Corners), AC
                                # Odds: B365H, B365D, B365A (Bet365)
                                home_stats={
                                    'shots': safe_float(row.get('HS')),
                                    'shots_on_target': safe_float(row.get('HST')),
                                    'corners': safe_float(row.get('HC')),
                                    'yellow_cards': safe_float(row.get('HY')),
                                    'red_cards': safe_float(row.get('HR'))
                                },
                                away_stats={
                                    'shots': safe_float(row.get('AS')),
                                    'shots_on_target': safe_float(row.get('AST')),
                                    'corners': safe_float(row.get('AC')),
                                    'yellow_cards': safe_float(row.get('AY')),
                                    'red_cards': safe_float(row.get('AR'))
                                },
                                prediction_data={
                                    'odds': {
                                        'home': safe_float(row.get('B365H')),
                                        'draw': safe_float(row.get('B365D')),
                                        'away': safe_float(row.get('B365A'))
                                    }
                                }
                            )
                            
                            db.add(fixture)
                            count += 1
                            
                        except Exception as e:
                            logger.warning(f"Skipping row: {e}")
                            continue
                            
                    db.commit()
                    logger.info(f"Imported {count} matches for {league_name} ({season})")
                    
                except Exception as e:
                    logger.error(f"Error importing {league_name}: {e}")
                    db.rollback() # Ensure rollback on error

    finally:
        db.close()

if __name__ == "__main__":
    import_data()
