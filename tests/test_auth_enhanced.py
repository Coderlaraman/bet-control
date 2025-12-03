"""
Tests para autenticación mejorada con seguridad robusta
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from app.main import app
from app.db.session import Base, get_db
from app.models.user import User, UserRole
from app.core.security import get_password_hash, validate_password_strength
from app.core.config import settings

# Configurar base de datos de prueba
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Crear y limpiar base de datos antes de cada test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestPasswordValidation:
    """Tests para validación de contraseñas robustas"""
    
    def test_password_too_short(self):
        """Contraseña muy corta debe fallar"""
        is_valid, message = validate_password_strength("Short1!")
        assert not is_valid
        assert "at least 8 characters" in message
    
    def test_password_no_uppercase(self):
        """Contraseña sin mayúsculas debe fallar"""
        is_valid, message = validate_password_strength("password123!")
        assert not is_valid
        assert "uppercase letter" in message
    
    def test_password_no_lowercase(self):
        """Contraseña sin minúsculas debe fallar"""
        is_valid, message = validate_password_strength("PASSWORD123!")
        assert not is_valid
        assert "lowercase letter" in message
    
    def test_password_no_number(self):
        """Contraseña sin números debe fallar"""
        is_valid, message = validate_password_strength("Password!")
        assert not is_valid
        assert "number" in message
    
    def test_password_no_special_char(self):
        """Contraseña sin caracteres especiales debe fallar"""
        is_valid, message = validate_password_strength("Password123")
        assert not is_valid
        assert "special character" in message
    
    def test_password_valid(self):
        """Contraseña válida debe pasar"""
        is_valid, message = validate_password_strength("ValidPass123!")
        assert is_valid
        assert message == "Password is valid"


class TestUserRegistration:
    """Tests para registro de usuarios"""
    
    def test_register_with_weak_password(self):
        """Registro con contraseña débil debe fallar"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "weak",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_register_with_strong_password(self):
        """Registro con contraseña robusta debe tener éxito"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "StrongPass123!",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["role"] == "user"  # Default role
    
    def test_register_duplicate_username(self):
        """Registro con username duplicado debe fallar"""
        # Primer registro
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test1@example.com",
                "password": "StrongPass123!",
                "full_name": "Test User"
            }
        )
        
        # Segundo registro con mismo username
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test2@example.com",
                "password": "StrongPass123!",
                "full_name": "Test User 2"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]


class TestLogin:
    """Tests para inicio de sesión"""
    
    def setup_method(self):
        """Crear usuario de prueba antes de cada test"""
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "loginuser",
                "email": "login@example.com",
                "password": "LoginPass123!",
                "full_name": "Login User"
            }
        )
    
    def test_login_success(self):
        """Login exitoso debe devolver tokens"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "loginuser",
                "password": "LoginPass123!"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self):
        """Login con contraseña incorrecta debe fallar"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "loginuser",
                "password": "WrongPass123!"
            }
        )
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self):
        """Login con usuario inexistente debe fallar"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent",
                "password": "SomePass123!"
            }
        )
        assert response.status_code == 401


class TestLoginAttemptLimiting:
    """Tests para límite de intentos de login"""
    
    def setup_method(self):
        """Crear usuario de prueba"""
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "limituser",
                "email": "limit@example.com",
                "password": "LimitPass123!",
                "full_name": "Limit User"
            }
        )
    
    def test_account_lockout_after_failed_attempts(self):
        """Cuenta debe bloquearse después de múltiples intentos fallidos"""
        # Hacer múltiples intentos fallidos
        for i in range(settings.MAX_LOGIN_ATTEMPTS):
            response = client.post(
                "/api/v1/auth/login",
                data={
                    "username": "limituser",
                    "password": "WrongPass123!"
                }
            )
            if i < settings.MAX_LOGIN_ATTEMPTS - 1:
                assert response.status_code == 401
            else:
                # El último intento debe bloquear la cuenta
                assert response.status_code == 423  # Locked
                assert "locked" in response.json()["detail"].lower()
    
    def test_successful_login_resets_attempts(self):
        """Login exitoso debe resetear contador de intentos"""
        # Hacer algunos intentos fallidos
        for i in range(2):
            client.post(
                "/api/v1/auth/login",
                data={
                    "username": "limituser",
                    "password": "WrongPass123!"
                }
            )
        
        # Login exitoso
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "limituser",
                "password": "LimitPass123!"
            }
        )
        assert response.status_code == 200
        
        # Verificar que los intentos se resetearon
        # (haciendo más intentos fallidos no debería bloquear inmediatamente)
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "limituser",
                "password": "WrongPass123!"
            }
        )
        assert response.status_code == 401  # No bloqueado aún


class TestPasswordChange:
    """Tests para cambio de contraseña"""
    
    def setup_method(self):
        """Crear usuario y obtener token"""
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "changeuser",
                "email": "change@example.com",
                "password": "OldPass123!",
                "full_name": "Change User"
            }
        )
        
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "changeuser",
                "password": "OldPass123!"
            }
        )
        self.token = response.json()["access_token"]
    
    def test_change_password_success(self):
        """Cambio de contraseña exitoso"""
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "old_password": "OldPass123!",
                "new_password": "NewPass123!"
            },
            headers={"Authorization": f"Bearer {self.token}"}
        )
        assert response.status_code == 200
        
        # Verificar que la nueva contraseña funciona
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "changeuser",
                "password": "NewPass123!"
            }
        )
        assert response.status_code == 200
    
    def test_change_password_wrong_old_password(self):
        """Cambio de contraseña con contraseña antigua incorrecta debe fallar"""
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "old_password": "WrongOldPass123!",
                "new_password": "NewPass123!"
            },
            headers={"Authorization": f"Bearer {self.token}"}
        )
        assert response.status_code == 400
    
    def test_change_password_weak_new_password(self):
        """Cambio a contraseña débil debe fallar"""
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "old_password": "OldPass123!",
                "new_password": "weak"
            },
            headers={"Authorization": f"Bearer {self.token}"}
        )
        assert response.status_code == 422  # Validation error


class TestRoleBasedAccess:
    """Tests para autorización basada en roles"""
    
    def test_user_has_default_role(self):
        """Usuario registrado debe tener rol USER por defecto"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "roleuser",
                "email": "role@example.com",
                "password": "RolePass123!",
                "full_name": "Role User"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "user"
    
    def test_admin_user_creation(self):
        """Verificar que se puede crear usuario admin (via base de datos)"""
        db = TestingSessionLocal()
        admin = User(
            username="admin",
            email="admin@example.com",
            password_hash=get_password_hash("AdminPass123!"),
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        assert admin.role == UserRole.ADMIN
        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
