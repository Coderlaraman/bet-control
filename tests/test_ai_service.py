import pytest
from app.services.ai_service import AIService

@pytest.mark.asyncio
async def test_get_daily_suggestions():
    service = AIService()
    suggestions = await service.get_daily_suggestions()
    
    assert isinstance(suggestions, list)
    if len(suggestions) > 0:
        prediction = suggestions[0]
        assert "prediction" in prediction
        assert "confidence_score" in prediction
        assert prediction["confidence_score"] >= 0.7
        assert "reasoning" in prediction
        assert len(prediction["reasoning"]) > 0

@pytest.mark.asyncio
async def test_analyze_match_logic():
    service = AIService()
    
    # Test case: Strong home team vs weak away team
    match = {
        "home_team": "Strong Team",
        "away_team": "Weak Team",
        "home_stats": {"wins_last_5": 5, "goals_avg": 3.0, "conceded_avg": 0.5},
        "away_stats": {"wins_last_5": 0, "goals_avg": 0.5, "conceded_avg": 2.5},
        "head_to_head": {"home_wins": 5, "draws": 0, "away_wins": 0}
    }
    
    analysis = service._analyze_match(match)
    assert analysis is not None
    assert analysis["prediction"] == "Home Win"
    assert analysis["confidence_score"] > 0.8

    # Test case: Balanced match (should return None or low confidence)
    balanced_match = {
        "home_team": "Team A",
        "away_team": "Team B",
        "home_stats": {"wins_last_5": 3, "goals_avg": 1.5, "conceded_avg": 1.0},
        "away_stats": {"wins_last_5": 3, "goals_avg": 1.5, "conceded_avg": 1.0},
        "head_to_head": {"home_wins": 2, "draws": 2, "away_wins": 2}
    }
    
    analysis = service._analyze_match(balanced_match)
    assert analysis is None
