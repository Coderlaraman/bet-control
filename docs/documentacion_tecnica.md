# Documentación Técnica - Sistema de Control de Apuestas RushBet

## Arquitectura del Sistema

### Stack Tecnológico

**Backend:**
- **Lenguaje**: Python 3.11+
- **Framework**: FastAPI 0.104.1
- **ORM**: SQLAlchemy 2.0.23
- **Base de Datos**: SQLite (desarrollo) / MySQL (producción)
- **Autenticación**: JWT (PyJWT)
- **Validación**: Pydantic
- **Logging**: Loguru

**Frontend:**
- **Framework**: React 18.2.0
- **Lenguaje**: TypeScript 5.3.2
- **UI**: Material-UI (MUI) 5.15.0
- **Estado**: React Context API
- **Routing**: React Router 6.20.1
- **HTTP Client**: Axios 1.6.2
- **Charts**: Recharts 2.8.0

### Estructura del Proyecto

```
BetControl/
├── app/                          # Backend FastAPI
│   ├── core/                     # Configuración y utilidades core
│   │   ├── config.py            # Configuración de la aplicación
│   │   ├── security.py          # Seguridad y autenticación
│   │   └── database.py          # Configuración de base de datos
│   ├── models/                   # Modelos SQLAlchemy
│   │   ├── user.py              # Modelo de usuario
│   │   ├── bet.py               # Modelos de apuestas
│   │   ├── bankroll.py          # Modelo de bankroll
│   │   └── sport.py             # Modelos de deportes
│   ├── schemas/                  # Esquemas Pydantic
│   │   ├── user.py              # Esquemas de usuario
│   │   ├── bet.py               # Esquemas de apuestas
│   │   └── bankroll.py          # Esquemas de bankroll
│   ├── services/                 # Lógica de negocio
│   │   ├── bet_service.py       # Servicio de apuestas
│   │   └── bankroll_service.py  # Servicio de bankroll
│   ├── api/                      # Endpoints de la API
│   │   ├── auth.py              # Autenticación
│   │   ├── bets.py              # CRUD de apuestas
│   │   └── bankroll.py          # Gestión de bankroll
│   └── main.py                   # Punto de entrada FastAPI
├── frontend/                     # Aplicación React
│   ├── src/
│   │   ├── components/          # Componentes React
│   │   ├── pages/               # Páginas de la aplicación
│   │   ├── services/            # Servicios de API
│   │   ├── context/             # Contexto de estado
│   │   └── utils/               # Utilidades
├── tests/                        # Tests unitarios
├── scripts/                      # Scripts de utilidad
└── docs/                        # Documentación
```

## Modelos de Datos

### Usuario (User)
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Apuesta (Bet)
```python
class Bet(Base):
    __tablename__ = "bets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bet_type_id = Column(Integer, ForeignKey("bet_types.id"), nullable=False)
    sport_id = Column(Integer, ForeignKey("sports.id"), nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"))
    league_id = Column(Integer, ForeignKey("leagues.id"))
    market_id = Column(Integer, ForeignKey("markets.id"))
    
    event_name = Column(String(200), nullable=False)
    event_date = Column(Date, nullable=False)
    event_time = Column(Time)
    home_team = Column(String(100))
    away_team = Column(String(100))
    
    bet_description = Column(String(500), nullable=False)
    odds = Column(Numeric(10, 2), nullable=False)
    stake = Column(Numeric(10, 2), nullable=False)
    potential_win = Column(Numeric(10, 2), nullable=False)
    
    status = Column(SQLAlchemyEnum(BetStatus), default=BetStatus.PENDING)
    result_amount = Column(Numeric(10, 2))
    settled_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
```

### Bankroll
```python
class BankrollConfig(Base):
    __tablename__ = "bankroll_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    initial_amount = Column(Numeric(10, 2), nullable=False)
    current_amount = Column(Numeric(10, 2), nullable=False)
    max_bet_percentage = Column(Numeric(5, 2), default=5.00)
    min_bet_amount = Column(Numeric(10, 2), default=10.00)
    max_bet_amount = Column(Numeric(10, 2), default=500.00)
    currency = Column(String(3), default="USD")
```

## API Endpoints

### Autenticación
- `POST /api/auth/register` - Registro de usuarios
- `POST /api/auth/login` - Inicio de sesión
- `GET /api/auth/me` - Perfil de usuario

### Apuestas
- `GET /api/bets/` - Listar apuestas del usuario
- `POST /api/bets/` - Crear nueva apuesta
- `GET /api/bets/{bet_id}` - Obtener detalles de apuesta
- `PUT /api/bets/{bet_id}` - Actualizar apuesta
- `DELETE /api/bets/{bet_id}` - Eliminar apuesta

### Bankroll
- `GET /api/bankroll/config` - Obtener configuración
- `PUT /api/bankroll/config` - Actualizar configuración
- `GET /api/bankroll/summary` - Resumen de bankroll
- `GET /api/bankroll/transactions` - Historial de transacciones

### Estadísticas
- `GET /api/bets/stats` - Estadísticas generales
- `GET /api/bets/stats/by-sport` - Estadísticas por deporte
- `GET /api/bets/stats/by-league` - Estadísticas por liga
- `GET /api/bets/stats/by-bet-type` - Estadísticas por tipo

## Lógica de Negocio

### Servicio de Apuestas (BetService)

**Crear Apuesta:**
```python
def create_bet(self, user_id: int, bet_data: BetCreate) -> Bet:
    # Validar montos con bankroll_service
    # Calcular ganancia potencial
    # Crear apuesta
    # Deducir del bankroll
    # Registrar transacción
```

**Actualizar Estado:**
```python
def update_bet(self, bet_id: int, bet_data: BetUpdate) -> Optional[Bet]:
    # Actualizar campos permitidos
    # Si cambia el estado a ganado/perdido:
    #   - Actualizar bankroll
    #   - Registrar transacción
    #   - Actualizar estadísticas
```

### Servicio de Bankroll (BankrollService)

**Validación de Apuestas:**
```python
def validate_bet_amount(self, user_id: int, amount: Decimal) -> bool:
    # Verificar fondos suficientes
    # Verificar límites configurados
    # Verificar porcentaje máximo por apuesta
```

**Ajuste de Bankroll:**
```python
def adjust_bankroll(self, user_id: int, amount: Decimal, transaction_type: str, bet_id: int = None):
    # Actualizar current_amount
    # Registrar transacción
    # Validar límites
```

## Seguridad

### Autenticación JWT
```python
# Crear token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

### Hash de Contraseñas
```python
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

## Configuración de Base de Datos

### SQLite (Desarrollo)
```python
SQLALCHEMY_DATABASE_URL = "sqlite:///./betcontrol.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
```

### MySQL (Producción)
```python
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
```

## Testing

### Tests Unitarios
```bash
# Ejecutar todos los tests
python -m pytest tests/ -v

# Ejecutar tests específicos
python -m pytest tests/test_bet_service.py -v
python -m pytest tests/test_bankroll_service.py -v
```

### Coverage
```bash
# Instalar coverage
pip install coverage

# Ejecutar con coverage
coverage run -m pytest tests/
coverage report
coverage html
```

## Despliegue

### Desarrollo Local
```bash
# Backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm start
```

### Producción
```bash
# Backend con Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Frontend build
cd frontend
npm run build
```

## Monitoreo y Logging

### Configuración de Logging
```python
from loguru import logger

logger.add("logs/bet_control.log", rotation="10 MB", retention="10 days")
logger.add("logs/errors.log", rotation="10 MB", level="ERROR")
```

### Métricas Importantes
- Tasa de acierto (win rate)
- ROI (Return on Investment)
- Volatilidad del bankroll
- Distribución de apuestas por deporte/liga

## Mantenimiento

### Backups de Base de Datos
```bash
# SQLite
sqlite3 betcontrol.db ".backup backup_$(date +%Y%m%d).db"

# MySQL
mysqldump -u root -p betcontrol > backup_$(date +%Y%m%d).sql
```

### Actualizaciones
1. Backup de base de datos
2. Actualizar código
3. Ejecutar migraciones
4. Reiniciar servicios
5. Verificar funcionamiento

## Escalabilidad

### Optimización de Consultas
- Índices en campos frecuentemente consultados
- Paginación para listas grandes
- Caché de consultas frecuentes

### Arquitectura de Microservicios
- Separación de servicios de apuestas, bankroll y estadísticas
- API Gateway para gestión de tráfico
- Base de datos por servicio

## Seguridad Adicional

### HTTPS y SSL
```python
# En producción, usar HTTPS
uvicorn app.main:app --ssl-keyfile=./key.pem --ssl-certfile=./cert.pem
```

### Rate Limiting
```python
from slowapi import Limiter
limiter = Limiter(key_func=lambda: "global")

@app.post("/api/bets/")
@limiter.limit("10/minute")
def create_bet(bet_data: BetCreate):
    pass
```

## Solución de Problemas

### Problemas Comunes

**Error de conexión a base de datos:**
- Verificar credenciales
- Verificar disponibilidad del servidor
- Verificar firewall

**Error de autenticación:**
- Verificar token JWT
- Verificar expiración del token
- Verificar permisos de usuario

**Error de validación:**
- Verificar esquemas Pydantic
- Verificar tipos de datos
- Verificar límites configurados

### Logs de Depuración
```python
logger.debug(f"User {user_id} creating bet with data: {bet_data}")
logger.info(f"Bet created successfully: {bet.id}")
logger.error(f"Error creating bet: {str(e)}")
```