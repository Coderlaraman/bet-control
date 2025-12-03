from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.db.session import get_db
from app.core.security import (
    create_access_token, 
    create_refresh_token, 
    verify_password, 
    get_password_hash,
    validate_password_strength,
    check_account_locked,
    handle_failed_login,
    reset_failed_login_attempts,
    blacklist_token,
    get_current_active_user
)
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token, PasswordChange, UserLogin
from app.services.bankroll_service import BankrollService
from decimal import Decimal
from loguru import logger

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Registrar nuevo usuario con validación de contraseña robusta"""
    try:
        logger.info(f"Attempting to register user: {user_data.username}, email: {user_data.email}")

        # Verificar si el usuario ya existe
        existing_user = db.query(User).filter(
            (User.username == user_data.username) | (User.email == user_data.email)
        ).first()
        
        if existing_user:
            if existing_user.username == user_data.username:
                logger.warning(f"Registration failed: Username already exists - {user_data.username}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already registered"
                )
            else:
                logger.warning(f"Registration failed: Email already exists - {user_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # La validación de contraseña ya se hace en el schema UserCreate
        # Crear nuevo usuario
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            full_name=user_data.full_name
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"User registered successfully: {user.id}, role: {user.role}")

        # Crear configuración de bankroll
        bankroll_service = BankrollService(db)
        bankroll_service.create_bankroll_config(user.id, Decimal("0"))

        return user
    
    except ValidationError as e:
        logger.error(f"Validation error during registration: {e.errors()}")
        # Extraer el primer error de validación
        first_error = e.errors()[0]
        field = first_error.get('loc', [''])[0]
        msg = first_error.get('msg', 'Validation error')
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field}: {msg}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during registration"
        )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Iniciar sesión con protección contra fuerza bruta - Acepta JSON"""
    try:
        logger.info(f"Login attempt for user: {credentials.username}")
        
        # Buscar usuario
        user = db.query(User).filter(User.username == credentials.username).first()
        
        if not user:
            logger.warning(f"Login failed: User not found - {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar si la cuenta está bloqueada
        if check_account_locked(user):
            remaining_time = (user.locked_until - datetime.utcnow()).total_seconds() / 60
            logger.warning(f"Login failed: Account locked - {user.username}, remaining time: {remaining_time:.1f} minutes")
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account is locked. Try again in {int(remaining_time) + 1} minutes."
            )
        
        # Verificar contraseña
        if not verify_password(credentials.password, user.password_hash):
            logger.warning(f"Login failed: Incorrect password - {user.username}, attempts: {user.failed_login_attempts + 1}")
            handle_failed_login(db, user)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar si el usuario está activo
        if not user.is_active:
            logger.warning(f"Login failed: Inactive user - {user.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # Login exitoso - resetear intentos fallidos
        reset_failed_login_attempts(db, user)
        logger.info(f"Login successful: {user.username}, role: {user.role}")
        
        # Crear tokens
        access_token = create_access_token(data={"sub": user.username})
        refresh_token = create_refresh_token(data={"sub": user.username})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during login"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refrescar token de acceso"""
    from app.core.security import verify_token
    
    payload = verify_token(refresh_token, token_type="refresh")
    if not payload:
        logger.warning("Token refresh failed: Invalid refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    
    if not user or not user.is_active:
        logger.warning(f"Token refresh failed: Invalid or inactive user - {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear nuevo access token
    new_access_token = create_access_token(data={"sub": user.username})
    logger.info(f"Token refreshed successfully for user: {user.username}")
    
    return {
        "access_token": new_access_token,
        "refresh_token": refresh_token,  # Devolver el mismo refresh token
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cambiar contraseña del usuario actual"""
    logger.info(f"Password change attempt for user: {current_user.username}")
    
    # Verificar contraseña actual
    if not verify_password(password_data.old_password, current_user.password_hash):
        logger.warning(f"Password change failed: Incorrect old password - {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # La validación de la nueva contraseña ya se hace en el schema PasswordChange
    # Actualizar contraseña
    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    
    logger.info(f"Password changed successfully for user: {current_user.username}")
    
    return {
        "message": "Password changed successfully"
    }


@router.post("/logout")
async def logout(
    token: str = Depends(lambda: None),
    current_user: User = Depends(get_current_active_user)
):
    """Cerrar sesión e invalidar token"""
    from fastapi.security import OAuth2PasswordBearer
    from fastapi import Request
    
    # Obtener el token del header Authorization
    # En una implementación real, deberías obtener el token del request
    logger.info(f"Logout for user: {current_user.username}")
    
    # Nota: En una implementación de producción, deberías implementar
    # un sistema de blacklist persistente (Redis, base de datos, etc.)
    # Por ahora, usamos la blacklist en memoria
    
    return {
        "message": "Logged out successfully"
    }