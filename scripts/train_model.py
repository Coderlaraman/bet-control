import os
import sys
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
from sqlalchemy.orm import Session
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from loguru import logger

# Add root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.fixture import Fixture

# Constants
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "services", "model.pkl")
COLUMNS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "services", "model_columns.pkl")

def load_data(db: Session) -> pd.DataFrame:
    """
    Load historical match data from database.
    """
    logger.info("Loading data from database...")
    # Fetch finished matches with scores
    # Ensure we only get matches that have Elo/Odds data (from GitHub import)
    fixtures = db.query(Fixture).filter(
        Fixture.status == 'FT',
        Fixture.home_score.isnot(None),
        Fixture.away_score.isnot(None),
        Fixture.home_elo.isnot(None) # Filter for rich data
    ).all()
    
    if not fixtures:
        logger.error("No historical data with Elo found.")
        sys.exit(1)
        
    data = []
    for f in fixtures:
        # Extract JSON stats safely
        h_stats = f.home_stats or {}
        a_stats = f.away_stats or {}
        
        data.append({
            'id': f.id,
            'date': f.event_date,
            'home_team': f.home_team,
            'away_team': f.away_team,
            'home_score': f.home_score,
            'away_score': f.away_score,
            
            # Elo
            'home_elo': f.home_elo,
            'away_elo': f.away_elo,
            
            # Odds
            'home_odds': f.home_odds,
            'draw_odds': f.draw_odds,
            'away_odds': f.away_odds,
            
            # Advanced Stats
            'home_shots': h_stats.get('shots'),
            'away_shots': a_stats.get('shots'),
            'home_corners': h_stats.get('corners'),
            'away_corners': a_stats.get('corners')
        })
        
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    logger.info(f"Loaded {len(df)} matches with Elo data.")
    return df

def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create predictive features from raw match data.
    """
    logger.info("Engineering features...")
    
    # 1. Target Variable
    conditions = [
        (df['home_score'] > df['away_score']),
        (df['home_score'] == df['away_score']),
        (df['home_score'] < df['away_score'])
    ]
    choices = [2, 1, 0]
    df['result'] = np.select(conditions, choices)
    
    # 2. Elo Difference (Strongest predictor)
    df['elo_diff'] = df['home_elo'] - df['away_elo']
    
    # 3. Implied Probabilities from Odds (Market consensus)
    # Fill missing odds with 1.0 to avoid division by zero, though we should filter them
    df['home_odds'] = df['home_odds'].fillna(0).replace(0, 100) 
    df['away_odds'] = df['away_odds'].fillna(0).replace(0, 100)
    
    df['prob_home'] = 1 / df['home_odds']
    df['prob_away'] = 1 / df['away_odds']
    
    # 4. Form (Rolling Averages of Stats)
    # We need to calculate stats *before* the match.
    
    # Stack data to have one row per team-match
    # Include shots and corners for form calculation
    home_df = df[['date', 'home_team', 'home_score', 'away_score', 'home_shots', 'home_corners', 'result']].copy()
    home_df.columns = ['date', 'team', 'goals_for', 'goals_against', 'shots_for', 'corners_for', 'match_result']
    home_df['is_home'] = 1
    home_df['points'] = home_df['match_result'].map({2: 3, 1: 1, 0: 0})
    
    away_df = df[['date', 'away_team', 'away_score', 'home_score', 'away_shots', 'away_corners', 'result']].copy()
    away_df.columns = ['date', 'team', 'goals_for', 'goals_against', 'shots_for', 'corners_for', 'match_result']
    away_df['is_home'] = 0
    away_df['points'] = away_df['match_result'].map({0: 3, 1: 1, 2: 0})
    
    team_stats = pd.concat([home_df, away_df]).sort_values(['team', 'date'])
    
    # Calculate rolling stats per team (Last 5 matches)
    rolling_cols = ['goals_for', 'goals_against', 'points', 'shots_for', 'corners_for']
    
    for col in rolling_cols:
        team_stats[f'last_5_{col}'] = team_stats.groupby('team')[col].transform(
            lambda x: x.shift(1).rolling(window=5, min_periods=1).mean()
        )
    
    # Prepare home stats to merge back
    home_stats = team_stats[team_stats['is_home'] == 1][['date', 'team', 'last_5_goals_for', 'last_5_points', 'last_5_shots_for']]
    home_stats.columns = ['date', 'home_team', 'home_form_goals', 'home_form_points', 'home_form_shots']
    
    # Prepare away stats
    away_stats = team_stats[team_stats['is_home'] == 0][['date', 'team', 'last_5_goals_for', 'last_5_points', 'last_5_shots_for']]
    away_stats.columns = ['date', 'away_team', 'away_form_goals', 'away_form_points', 'away_form_shots']
    
    # Merge
    df = pd.merge(df, home_stats, on=['date', 'home_team'], how='left')
    df = pd.merge(df, away_stats, on=['date', 'away_team'], how='left')
    
    # Fill NaNs (for first matches of season)
    df = df.fillna(0)
    
    return df

def train_model(df: pd.DataFrame):
    """
    Train XGBoost model with V3 features.
    """
    # Features V3: Elo + Odds + Form + Stats
    features = [
        'elo_diff',
        'prob_home', 'prob_away',
        'home_form_points', 'away_form_points',
        'home_form_goals', 'away_form_goals',
        'home_form_shots', 'away_form_shots'
    ]
    
    X = df[features]
    y = df['result']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    logger.info(f"Training with {len(X)} samples and {len(features)} features...")
    
    # XGBoost Configuration
    # objective='multi:softprob' for multiclass probability
    # num_class=3 for Home/Draw/Away
    clf = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,            # Slightly lower than RF's 10, XGB builds trees differently
        learning_rate=0.05,     # Lower learning rate for better generalization
        subsample=0.8,          # Subsample rows to prevent overfitting
        colsample_bytree=0.8,   # Subsample columns
        objective='multi:softprob',
        num_class=3,
        random_state=42,
        eval_metric='mlogloss'
    )
    
    clf.fit(X_train, y_train)
    
    # Evaluate
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    logger.info(f"Model Accuracy: {acc:.2f}")
    logger.info("\n" + classification_report(y_test, y_pred, target_names=['Away Win', 'Draw', 'Home Win']))
    
    # Feature Importance
    importances = pd.DataFrame({'feature': features, 'importance': clf.feature_importances_})
    logger.info("\nTop Features:\n" + str(importances.sort_values('importance', ascending=False)))
    
    # Save model
    joblib.dump(clf, MODEL_PATH)
    joblib.dump(features, COLUMNS_PATH)
    logger.info("Model V3 (XGBoost) saved successfully.")

def main():
    db = SessionLocal()
    try:
        df = load_data(db)
        df_processed = feature_engineering(df)
        train_model(df_processed)
    finally:
        db.close()

if __name__ == "__main__":
    main()
