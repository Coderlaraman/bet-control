import asyncio
import sys
import os
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger
from sqlalchemy.orm import Session

# Add root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.services.ai_service import AIService
from app.models.fixture import Fixture

async def test_predictions():
    """
    Test script to fetch upcoming matches and generate predictions using the trained model.
    """
    logger.info("Starting Prediction Test...")
    
    db = SessionLocal()
    ai_service = AIService()
    
    try:
        # Test a known active date: Saturday, Dec 14, 2024
        target_date = datetime(2024, 12, 14).date()
        logger.info(f"--- Testing Predictions for {target_date} (Offline Mode) ---")
        
        # 1. Fetch fixtures from DB directly
        fixtures = db.query(Fixture).filter(
            Fixture.event_date >= datetime.combine(target_date, datetime.min.time()),
            Fixture.event_date < datetime.combine(target_date + timedelta(days=1), datetime.min.time())
        ).all()
        
        if not fixtures:
            logger.warning("No fixtures found in DB. Cannot test offline.")
            return

        logger.info(f"Found {len(fixtures)} fixtures in DB. Running AI Analysis...")
        
        predictions = []
        for f in fixtures:
            # Convert Fixture to dict format expected by _analyze_match
            match_data = {
                "id": f.id,
                "home_team": f.home_team,
                "away_team": f.away_team,
                "date": f.event_date.isoformat(),
                "home_stats": f.home_stats or {},
                "away_stats": f.away_stats or {},
                "head_to_head": f.h2h_data or {"home_wins": 0, "draws": 0, "away_wins": 0},
                # We might need to pass odds if they are in columns
                "home_odds": f.home_odds,
                "away_odds": f.away_odds,
                "draw_odds": f.draw_odds
            }
            
            # Run Analysis
            analysis = ai_service._analyze_match(match_data, db)
            
            if analysis:
                # Combine match info with prediction
                result = {
                    "home_team": f.home_team,
                    "away_team": f.away_team,
                    "league": f.league.name if f.league else "Unknown",
                    "date": f.event_date.isoformat(),
                    **analysis
                }
                predictions.append(result)
        
        # Sort and print
        predictions = sorted(predictions, key=lambda x: x['confidence_score'], reverse=True)
        print_results(predictions, f"{target_date}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        db.close()

def print_results(suggestions, label):
    print(f"\n{'='*20} {label} PREDICTIONS {'='*20}")
    if not suggestions:
        print("No matches found.")
        return

    for s in suggestions:
        print(f"\nMatch: {s.get('home_team')} vs {s.get('away_team')}")
        print(f"League: {s.get('league')}")
        print(f"Date: {s.get('date')}")
        
        # Debug: Print all keys if prediction is missing
        if 'prediction' not in s:
            print(f"WARNING: 'prediction' key missing. Keys found: {list(s.keys())}")
            print(f"Raw Data: {s}")
            continue
            
        print(f"Prediction: {s['prediction']}")
        print(f"Confidence: {s.get('confidence_score', 0):.2f}")
        print(f"Reasoning:")
        if 'reasoning' in s:
            for r in s['reasoning']:
                print(f"  - {r}")
        
        print("-" * 40)

if __name__ == "__main__":
    # Run async loop
    asyncio.run(test_predictions())
