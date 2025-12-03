import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger

# Add root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.fixture import Fixture

# Config
MATCHES_CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               "Club-Football-Match-Data-2000-2025-main", "Club-Football-Match-Data-2000-2025-main", "data", "Matches.csv")

# Target Leagues (Country Code + Division)
# E0: Premier League, SP1: La Liga, I1: Serie A, D1: Bundesliga, F1: Ligue 1
TARGET_LEAGUES = ["E0", "SP1", "I1", "D1", "F1"]
START_DATE = "2020-08-01" # Import from 2020 onwards

def safe_float(val):
    if pd.isna(val):
        return None
    try:
        return float(val)
    except:
        return None

def safe_int(val):
    if pd.isna(val):
        return None
    try:
        return int(val)
    except:
        return None

def import_matches():
    if not os.path.exists(MATCHES_CSV_PATH):
        logger.error(f"Matches.csv not found at {MATCHES_CSV_PATH}")
        return

    logger.info("Reading Matches.csv...")
    # Read CSV with low memory mode or chunking if it's huge, but 50MB is fine for memory
    df = pd.read_csv(MATCHES_CSV_PATH)
    
    # Filter Leagues
    df = df[df['Division'].isin(TARGET_LEAGUES)]
    logger.info(f"Filtered by leagues: {len(df)} matches.")
    
    # Filter Date
    df['MatchDate'] = pd.to_datetime(df['MatchDate'])
    df = df[df['MatchDate'] >= pd.to_datetime(START_DATE)]
    logger.info(f"Filtered by date (>= {START_DATE}): {len(df)} matches.")
    
    db = SessionLocal()
    count = 0
    
    try:
        for _, row in df.iterrows():
            try:
                # Generate ID
                event_date = row['MatchDate']
                # MatchTime is HH:MM:SS
                if not pd.isna(row['MatchTime']):
                    try:
                        time_parts = str(row['MatchTime']).split(':')
                        event_date = event_date.replace(hour=int(time_parts[0]), minute=int(time_parts[1]))
                    except:
                        pass # Keep date only if time fails
                
                home_team = row['HomeTeam'].strip()
                away_team = row['AwayTeam'].strip()
                
                # Unique ID
                safe_home = "".join(c for c in home_team if c.isalnum())[:3]
                safe_away = "".join(c for c in away_team if c.isalnum())[:3]
                fixture_id = f"gh_{event_date.strftime('%Y%m%d')}_{safe_home}_{safe_away}"
                
                # Check existence
                existing = db.query(Fixture).filter(Fixture.id == fixture_id).first()
                if existing:
                    continue # Skip duplicates
                
                # Build Fixture
                fixture = Fixture(
                    id=fixture_id,
                    home_team=home_team,
                    away_team=away_team,
                    event_date=event_date,
                    status='FT',
                    home_score=safe_int(row['FTHome']),
                    away_score=safe_int(row['FTAway']),
                    
                    # New Elo & Odds Columns
                    home_elo=safe_float(row.get('HomeElo')),
                    away_elo=safe_float(row.get('AwayElo')),
                    home_odds=safe_float(row.get('OddHome')),
                    draw_odds=safe_float(row.get('OddDraw')),
                    away_odds=safe_float(row.get('OddAway')),
                    
                    # Stats in JSON
                    home_stats={
                        'shots': safe_float(row.get('HomeShots')),
                        'shots_on_target': safe_float(row.get('HomeTarget')),
                        'corners': safe_float(row.get('HomeCorners')),
                        'yellow_cards': safe_float(row.get('HomeYellow')),
                        'red_cards': safe_float(row.get('HomeRed')),
                        'form_5': safe_int(row.get('Form5Home'))
                    },
                    away_stats={
                        'shots': safe_float(row.get('AwayShots')),
                        'shots_on_target': safe_float(row.get('AwayTarget')),
                        'corners': safe_float(row.get('AwayCorners')),
                        'yellow_cards': safe_float(row.get('AwayYellow')),
                        'red_cards': safe_float(row.get('AwayRed')),
                        'form_5': safe_int(row.get('Form5Away'))
                    }
                )
                
                db.add(fixture)
                count += 1
                
                if count % 1000 == 0:
                    db.commit()
                    logger.info(f"Imported {count} matches...")
                    
            except Exception as e:
                logger.warning(f"Error processing row: {e}")
                continue
                
        db.commit()
        logger.info(f"Successfully imported {count} matches from GitHub dataset.")
        
    except Exception as e:
        logger.error(f"Import failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import_matches()
