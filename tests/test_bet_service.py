import pytest
from decimal import Decimal
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.models.user import User
from app.models.bet import Bet, BetType, Market, BetStatus
from app.models.sport import Sport
from app.models.bankroll import BankrollConfig
from app.services.bet_service import BetService
from app.schemas.bet import BetCreate, BetUpdate


# Configuración de base de datos de prueba
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Crear base de datos de prueba para cada test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def user(db):
    """Crear usuario de prueba"""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        full_name="Test User"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def bankroll_config(db, user):
    """Crear configuración de bankroll de prueba"""
    config = BankrollConfig(
        user_id=user.id,
        initial_amount=Decimal("1000.00"),
        current_amount=Decimal("1000.00"),
        max_bet_percentage=Decimal("5.00"),
        min_bet_amount=Decimal("10.00"),
        max_bet_amount=Decimal("500.00")
    )
    db.add(config)
    db.commit()
    return config


@pytest.fixture
def test_data(db):
    """Crear datos de prueba"""
    # Crear tipos de apuesta
    bet_type = BetType(name="Single", description="Single bet")
    db.add(bet_type)
    
    # Crear deportes
    sport = Sport(name="Soccer", code="SOC")
    db.add(sport)
    
    # Crear mercados
    market = Market(name="Match Winner", code="MW", description="Match winner market")
    db.add(market)
    
    db.commit()
    return {"bet_type": bet_type, "sport": sport, "market": market}


@pytest.fixture
def bet_service(db):
    """Crear servicio de apuestas"""
    return BetService(db)


class TestBetService:
    
    def test_create_bet_success(self, bet_service, user, test_data, bankroll_config):
        """Test crear apuesta exitosamente"""
        bet_data = BetCreate(
            bet_type_id=test_data["bet_type"].id,
            sport_id=test_data["sport"].id,
            market_id=test_data["market"].id,
            event_name="Real Madrid vs Barcelona",
            event_date=datetime(2024, 12, 1),
            event_time=datetime(2024, 12, 1, 20, 0),
            home_team="Real Madrid",
            away_team="Barcelona",
            bet_description="Real Madrid to win",
            odds=Decimal("2.50"),
            stake=Decimal("50.00")
        )
        
        bet = bet_service.create_bet(user.id, bet_data)
        
        assert bet.user_id == user.id
        assert bet.bet_type_id == test_data["bet_type"].id
        assert bet.sport_id == test_data["sport"].id
        assert bet.event_name == "Real Madrid vs Barcelona"
        assert bet.odds == Decimal("2.50")
        assert bet.stake == Decimal("50.00")
        assert bet.potential_win == Decimal("125.00")  # 50 * 2.5
        assert bet.status == BetStatus.PENDING
    
    def test_get_bet_by_id(self, bet_service, user, test_data):
        """Test obtener apuesta por ID"""
        bet_data = BetCreate(
            bet_type_id=test_data["bet_type"].id,
            sport_id=test_data["sport"].id,
            event_name="Test Event",
            event_date=datetime(2024, 12, 1),
            bet_description="Test bet",
            odds=Decimal("2.00"),
            stake=Decimal("30.00")
        )
        
        created_bet = bet_service.create_bet(user.id, bet_data)
        retrieved_bet = bet_service.get_bet_by_id(created_bet.id)
        
        assert retrieved_bet is not None
        assert retrieved_bet.id == created_bet.id
        assert retrieved_bet.event_name == "Test Event"
    
    def test_get_user_bets(self, bet_service, user, test_data):
        """Test obtener apuestas de usuario"""
        # Crear múltiples apuestas
        for i in range(3):
            bet_data = BetCreate(
                bet_type_id=test_data["bet_type"].id,
                sport_id=test_data["sport"].id,
                event_name=f"Event {i}",
                event_date=datetime(2024, 12, 1),
                bet_description=f"Bet {i}",
                odds=Decimal("2.00"),
                stake=Decimal("20.00")
            )
            bet_service.create_bet(user.id, bet_data)
        
        user_bets = bet_service.get_user_bets(user.id)
        
        assert len(user_bets) == 3
        assert all(bet.user_id == user.id for bet in user_bets)
    
    def test_update_bet_status(self, bet_service, user, test_data):
        """Test actualizar estado de apuesta"""
        bet_data = BetCreate(
            bet_type_id=test_data["bet_type"].id,
            sport_id=test_data["sport"].id,
            event_name="Test Event",
            event_date=datetime(2024, 12, 1),
            bet_description="Test bet",
            odds=Decimal("2.00"),
            stake=Decimal("30.00")
        )
        
        bet = bet_service.create_bet(user.id, bet_data)
        
        # Actualizar estado a "won"
        updated_bet = bet_service.update_bet(bet.id, BetUpdate(status="won", result_amount=Decimal("60.00")))
        
        assert updated_bet.status == BetStatus.WON
        assert updated_bet.result_amount == Decimal("60.00")
    
    def test_delete_bet(self, bet_service, user, test_data):
        """Test eliminar apuesta"""
        bet_data = BetCreate(
            bet_type_id=test_data["bet_type"].id,
            sport_id=test_data["sport"].id,
            event_name="Test Event",
            event_date=datetime(2024, 12, 1),
            bet_description="Test bet",
            odds=Decimal("2.00"),
            stake=Decimal("30.00")
        )
        
        bet = bet_service.create_bet(user.id, bet_data)
        bet_id = bet.id
        
        # Eliminar apuesta
        result = bet_service.delete_bet(bet_id)
        assert result is True
        
        # Verificar que ya no existe
        deleted_bet = bet_service.get_bet_by_id(bet_id)
        assert deleted_bet is None
    
    def test_get_user_betting_stats(self, bet_service, user, test_data):
        """Test obtener estadísticas de apuestas de usuario"""
        # Crear apuestas con diferentes resultados
        bets_data = [
            {"status": "won", "stake": Decimal("50.00"), "result_amount": Decimal("100.00")},
            {"status": "won", "stake": Decimal("30.00"), "result_amount": Decimal("60.00")},
            {"status": "lost", "stake": Decimal("40.00"), "result_amount": Decimal("0.00")},
            {"status": "pending", "stake": Decimal("25.00"), "result_amount": None},
        ]
        
        for bet_info in bets_data:
            bet_data = BetCreate(
                bet_type_id=test_data["bet_type"].id,
                sport_id=test_data["sport"].id,
                event_name="Test Event",
                event_date=datetime(2024, 12, 1),
                bet_description="Test bet",
                odds=Decimal("2.00"),
                stake=bet_info["stake"]
            )
            bet = bet_service.create_bet(user.id, bet_data)
            bet_service.update_bet(bet.id, BetUpdate(
                status=bet_info["status"],
                result_amount=bet_info["result_amount"]
            ))
        
        stats = bet_service.get_user_betting_stats(user.id)
        
        assert stats["total_bets"] == 4
        assert stats["won_bets"] == 2
        assert stats["lost_bets"] == 1
        assert stats["pending_bets"] == 1
        assert stats["total_staked"] == 145.00
        assert stats["total_won"] == 160.00
        assert stats["total_profit"] == 15.00
        assert round(stats["win_rate"], 2) == 66.67  # 2 won / 3 settled
        assert round(stats["roi"], 2) == 10.34  # (15 / 145) * 100