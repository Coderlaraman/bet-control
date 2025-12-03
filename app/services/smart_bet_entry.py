import spacy
import re
from typing import Dict, Any, Optional
from loguru import logger
from datetime import datetime, timedelta

class SmartBetEntryService:
    """
    Service to parse natural language bet descriptions into structured bet data.
    Uses NLP and Regex patterns to extract entities.
    """
    
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            self.nlp = None
            
        # Mapping of common market synonyms to IDs or standardized names
        self.market_keywords = {
            "win": "Match Winner",
            "winner": "Match Winner",
            "victory": "Match Winner",
            "beats": "Match Winner",
            "draw": "Match Winner",
            "tie": "Match Winner",
            "over": "Over/Under",
            "under": "Over/Under",
            "goals": "Over/Under",
            "score": "Correct Score",
            "btts": "Both Teams To Score",
            "both score": "Both Teams To Score"
        }

    def parse_bet_description(self, text: str) -> Dict[str, Any]:
        """
        Parse a natural language string into structured bet data.
        Example Input: "I bet 50 on Real Madrid to beat Barcelona"
        """
        doc = self.nlp(text.lower()) if self.nlp else None
        
        structured_data = {
            "stake": None,
            "home_team": None,
            "away_team": None,
            "market": "Match Winner", # Default
            "selection": None,
            "original_text": text
        }
        
        # 1. Extract Stake (Money)
        # Look for currency symbols or numbers followed by currency words
        stake_pattern = r"(\d+(?:\.\d{1,2})?)\s*(?:dollars|euros|usd|eur|\$)|(?:\$|€)\s*(\d+(?:\.\d{1,2})?)"
        stake_match = re.search(stake_pattern, text.lower())
        
        if stake_match:
            # Group 1 or Group 2
            amount = stake_match.group(1) or stake_match.group(2)
            structured_data["stake"] = float(amount)
        else:
            # Fallback: Look for just numbers if the context implies betting
            # "bet 50"
            simple_stake = re.search(r"bet\s+(\d+)", text.lower())
            if simple_stake:
                structured_data["stake"] = float(simple_stake.group(1))

        # 2. Extract Teams (Entities)
        # Use Spacy NER for ORG (Organizations) or GPE (Geopolitical Entities)
        teams = []
        if doc:
            for ent in doc.ents:
                if ent.label_ in ["ORG", "GPE", "PERSON"]:
                    if ent.text not in ["bet", "usd", "eur", "money", "game", "match"]:
                        teams.append(ent.text.title())
        else:
            m = re.search(r"(.+?)\s+to\s+(?:beat|win|defeat)\s+(.+)", text, flags=re.I)
            if m:
                teams.append(m.group(1).strip().title())
                teams.append(m.group(2).strip().title())
            else:
                m2 = re.search(r"(.+?)\s+vs\.?\s+(.+)", text, flags=re.I)
                if m2:
                    teams.append(m2.group(1).strip().title())
                    teams.append(m2.group(2).strip().title())
        
        if len(teams) >= 1:
            structured_data["selection"] = teams[0] # Assuming first entity is the pick
            structured_data["home_team"] = teams[0]
        
        if len(teams) >= 2:
            structured_data["away_team"] = teams[1]
            
        # 3. Infer Market
        if doc:
            for token in doc:
                if token.text in self.market_keywords:
                    structured_data["market"] = self.market_keywords[token.text]
                    break
                
        # 4. Refine Selection logic
        # "Real Madrid to beat Barcelona" -> Selection: Real Madrid
        # "Over 2.5 goals in Real vs Barca" -> Selection: Over 2.5
        
        if "over" in text.lower() or "under" in text.lower():
            structured_data["market"] = "Over/Under"
            ou_match = re.search(r"(over|under)\s*(\d+\.?\d*)", text.lower())
            if ou_match:
                structured_data["selection"] = f"{ou_match.group(1).title()} {ou_match.group(2)}"
                
        return structured_data
