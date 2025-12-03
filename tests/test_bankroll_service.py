import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.models.user import User
from app.models.bankroll import BankrollConfig, BankrollTransaction, TransactionType
from app.services.bankroll_service import BankrollService
from app.core.exceptions import InsufficientFundsError, InvalidBetAmountError


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
    db.refresh(config)
    return config


@pytest.fixture
def bankroll_service(db):
    """Crear servicio de bankroll"""
    return BankrollService(db)


class TestBankrollService:
    
    def test_create_bankroll_config(self, bankroll_service, user):
        """Test crear configuración de bankroll"""
        config = bankroll_service.create_bankroll_config(user.id, Decimal("1000.00"))
        
        assert config.user_id == user.id
        assert config.initial_amount == Decimal("1000.00")
        assert config.current_amount == Decimal("1000.00")
        assert config.max_bet_percentage == Decimal("5.00")
    
    def test_validate_bet_amount_success(self, bankroll_service, user, bankroll_config):
        """Test validar monto de apuesta exitoso"""
        # Apuesta válida dentro de los límites
        result = bankroll_service.validate_bet_amount(user.id, Decimal("50.00"))
        assert result is True
    
    def test_validate_bet_amount_insufficient_funds(self, bankroll_service, user, bankroll_config):
        """Test validar monto con fondos insuficientes"""
        with pytest.raises(InsufficientFundsError):
            bankroll_service.validate_bet_amount(user.id, Decimal("2000.00"))
    
    def test_validate_bet_amount_below_minimum(self, bankroll_service, user, bankroll_config):
        """Test validar monto por debajo del mínimo"""
        with pytest.raises(InvalidBetAmountError):
            bankroll_service.validate_bet_amount(user.id, Decimal("5.00"))
    
    def test_validate_bet_amount_exceeds_percentage(self, bankroll_service, user, bankroll_config):
        """Test validar monto que excede el porcentaje máximo"""
        # 5% de 1000 = 50, así que 60 debería fallar
        with pytest.raises(InvalidBetAmountError):
            bankroll_service.validate_bet_amount(user.id, Decimal("60.00"))
    
    def test_validate_bet_amount_exceeds_maximum(self, bankroll_service, user, bankroll_config):
        """Test validar monto que excede el máximo absoluto"""
        with pytest.raises(InvalidBetAmountError):
            bankroll_service.validate_bet_amount(user.id, Decimal("600.00"))
    
    def test_place_bet_deduction(self, bankroll_service, user, bankroll_config):
        """Test deducción de apuesta"""
        transaction = bankroll_service.place_bet_deduction(user.id, 1, Decimal("50.00"))
        
        assert transaction.user_id == user.id
        assert transaction.transaction_type == TransactionType.BET_PLACED
        assert transaction.amount == Decimal("-50.00")
        assert transaction.balance_before == Decimal("1000.00")
        assert transaction.balance_after == Decimal("950.00")
        
        # Verificar que el bankroll se actualizó
        config = bankroll_service.get_user_bankroll_config(user.id)
        assert config.current_amount == Decimal("950.00")
    
    def test_settle_bet_win(self, bankroll_service, user, bankroll_config):
        """Test procesar apuesta ganadora"""
        # Primero deducir la apuesta
        bankroll_service.place_bet_deduction(user.id, 1, Decimal("50.00"))
        
        # Luego procesar la ganancia
        win_amount = Decimal("125.00")  # 50 * 2.5
        transaction = bankroll_service.settle_bet_win(user.id, 1, win_amount)
        
        assert transaction.user_id == user.id
        assert transaction.transaction_type == TransactionType.BET_WON
        assert transaction.amount == win_amount
        assert transaction.balance_before == Decimal("950.00")
        assert transaction.balance_after == Decimal("1075.00")
        
        # Verificar que el bankroll se actualizó
        config = bankroll_service.get_user_bankroll_config(user.id)
        assert config.current_amount == Decimal("1075.00")
    
    def test_settle_bet_void(self, bankroll_service, user, bankroll_config):
        """Test procesar apuesta anulada"""
        # Primero deducir la apuesta
        bankroll_service.place_bet_deduction(user.id, 1, Decimal("50.00"))
        
        # Luego procesar la anulación
        transaction = bankroll_service.settle_bet_void(user.id, 1, Decimal("50.00"))
        
        assert transaction.user_id == user.id
        assert transaction.transaction_type == TransactionType.BET_VOID
        assert transaction.amount == Decimal("50.00")
        assert transaction.balance_before == Decimal("950.00")
        assert transaction.balance_after == Decimal("1000.00")
        
        # Verificar que el bankroll se restauró
        config = bankroll_service.get_user_bankroll_config(user.id)
        assert config.current_amount == Decimal("1000.00")
    
    def test_get_bankroll_summary(self, bankroll_service, user, bankroll_config):
        """Test obtener resumen de bankroll"""
        # Crear algunas transacciones
        bankroll_service.place_bet_deduction(user.id, 1, Decimal("50.00"))
        bankroll_service.settle_bet_win(user.id, 1, Decimal("125.00"))
        
        summary = bankroll_service.get_bankroll_summary(user.id)
        
        assert summary is not None
        assert summary["current_amount"] == 1075.00
        assert summary["initial_amount"] == 1000.00
        assert summary["profit_loss"] == 75.00
        assert len(summary["recent_transactions"]) == 2