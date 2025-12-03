from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "BetControl RushBet"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "betcontrol")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 15
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost:8080",
    ]
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 200
    
    # Bankroll settings
    DEFAULT_MAX_BET_PERCENTAGE: float = 5.0  # 5% of bankroll
    DEFAULT_MIN_BET_AMOUNT: float = 1.0
    DEFAULT_MAX_BET_AMOUNT: float = 1000.0
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # Email (opcional)
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # API-Football (para predicciones AI)
    API_FOOTBALL_KEY: Optional[str] = os.getenv("API_FOOTBALL_KEY")
    API_FOOTBALL_HOST: str = os.getenv("API_FOOTBALL_HOST", "v3.football.api-sports.io")
    
    @property
    def DATABASE_URL(self) -> str:
        # Use SQLite for development if DB_HOST is 'sqlite'
        if self.DB_HOST == 'sqlite':
            return f"sqlite:///./{self.DB_NAME}.db"
        # Otherwise use MySQL
        return f"mysql+mysqlconnector://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()