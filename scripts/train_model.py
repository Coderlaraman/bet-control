import os
import sys
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
from sqlalchemy.orm import Session
from sklearn.ensemble import RandomForestClassifier
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
    fixtures = db.query(Fixture).filter(
        Fixture.status == 'FT',
        Fixture.home_score.isnot(None),
        Fixture.away_score.isnot(None)
    ).all()
    
    if not fixtures:
        logger.error("No historical data found. Run backfill script first.")
        sys.exit(1)
        
    data = []
    for f in fixtures:
        data.append({
            'id': f.id,
            'date': f.event_date,
            'home_team': f.home_team,
            'away_team': f.away_team,
            'home_score': f.home_score,
            'away_score': f.away_score,
            'league_id': f.league_id # Might be None if not linked properly, but useful if we have it
        })
        
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    logger.info(f"Loaded {len(df)} matches.")
    return df

def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create predictive features from raw match data.
    This is the most critical part for model performance.
    """
    logger.info("Engineering features...")
    
    # 1. Target Variable: Result (0: Away Win, 1: Draw, 2: Home Win)
    conditions = [
        (df['home_score'] > df['away_score']),
        (df['home_score'] == df['away_score']),
        (df['home_score'] < df['away_score'])
    ]
    choices = [2, 1, 0]
    df['result'] = np.select(conditions, choices)
    
    # 2. Team Stats Calculation (Rolling Averages)
    # We need to calculate stats *before* the match happened to avoid data leakage.
    
    # Stack data to have one row per team-match to calculate form easily
    home_df = df[['date', 'home_team', 'home_score', 'away_score', 'result']].copy()
    home_df.columns = ['date', 'team', 'goals_for', 'goals_against', 'match_result']
    home_df['is_home'] = 1
    home_df['points'] = home_df['match_result'].map({2: 3, 1: 1, 0: 0})
    
    away_df = df[['date', 'away_team', 'away_score', 'home_score', 'result']].copy()
    away_df.columns = ['date', 'team', 'goals_for', 'goals_against', 'match_result']
    away_df['is_home'] = 0
    away_df['points'] = away_df['match_result'].map({0: 3, 1: 1, 2: 0})
    
    team_stats = pd.concat([home_df, away_df]).sort_values(['team', 'date'])
    
    # Calculate rolling stats per team (Last 5 matches)
    # shift(1) ensures we don't include the current match in the average
    rolling_cols = ['goals_for', 'goals_against', 'points']
    
    for col in rolling_cols:
        team_stats[f'last_5_{col}'] = team_stats.groupby('team')[col].transform(
            lambda x: x.shift(1).rolling(window=5, min_periods=1).mean()
        )
        
    # 3. Cumulative Season Points (Long Term Context)
    # Calculate cumulative sum of points
    team_stats['season_points'] = team_stats.groupby('team')['points'].transform(
        lambda x: x.shift(1).cumsum()
    )
    
    # Merge back to main dataframe
    # We need to merge twice: once for home team stats, once for away team stats
    
    # Prepare home stats
    home_stats = team_stats[team_stats['is_home'] == 1][['date', 'team', 'last_5_goals_for', 'last_5_goals_against', 'last_5_points', 'season_points']]
    home_stats.columns = ['date', 'home_team', 'home_form_goals', 'home_form_defense', 'home_form_points', 'home_season_points']
    
    # Prepare away stats
    away_stats = team_stats[team_stats['is_home'] == 0][['date', 'team', 'last_5_goals_for', 'last_5_goals_against', 'last_5_points', 'season_points']]
    away_stats.columns = ['date', 'away_team', 'away_form_goals', 'away_form_defense', 'away_form_points', 'away_season_points']
    
    # Merge
    logger.info(f"Merging stats... df shape: {df.shape}")
    logger.info(f"Home stats shape: {home_stats.shape}")
    
    df = pd.merge(df, home_stats, on=['date', 'home_team'], how='left')
    df = pd.merge(df, away_stats, on=['date', 'away_team'], how='left')
    
    logger.info(f"Shape after merge: {df.shape}")
    
    # Fill NaNs instead of dropping everything
    # For form, if we don't have history, we assume average performance
    # Or simpler: fill with 0 or global mean. 
    # Let's fill with 0 to be safe if mean is NaN
    cols_to_fill = [
        'home_form_goals', 'home_form_defense', 'home_form_points',
        'away_form_goals', 'away_form_defense', 'away_form_points',
        'home_season_points', 'away_season_points'
    ]
    
    for col in cols_to_fill:
        if col in df.columns:
             df[col] = df[col].fillna(0)
             
    # Add differential features (User requested: League Table Impact)
    # Difference in season points (proxy for table position gap)
    df['points_diff'] = df['home_season_points'] - df['away_season_points']

    # Drop rows where we still have NaNs (should be none or very few)
    # Check columns relevant for training
    # Note: points_diff is derived, so no need to check
    df = df.dropna(subset=cols_to_fill + ['result'])
    
    logger.info(f"Features ready. Dataset size after processing: {len(df)}")
    return df

def train_model(df: pd.DataFrame):
    """
    Train Random Forest model.
    """
    # Features to use for training
    features = [
        'home_form_goals', 'home_form_defense', 'home_form_points',
        'away_form_goals', 'away_form_defense', 'away_form_points',
        'home_season_points', 'away_season_points', 'points_diff'
    ]
    
    X = df[features]
    y = df['result']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    logger.info("Training Random Forest Classifier...")
    clf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    clf.fit(X_train, y_train)
    
    # Evaluate
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    logger.info(f"Model Accuracy: {acc:.2f}")
    logger.info("\n" + classification_report(y_test, y_pred, target_names=['Away Win', 'Draw', 'Home Win']))
    
    # Save model
    logger.info(f"Saving model to {MODEL_PATH}...")
    joblib.dump(clf, MODEL_PATH)
    joblib.dump(features, COLUMNS_PATH)
    logger.info("Model saved successfully.")

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
