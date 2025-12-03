# Arquitectura del Sistema de Control de Apuestas RushBet

## Arquitectura de 3 Capas

### 1. Capa de Presentación
- **Web Frontend**: React con TypeScript
- **Desktop App**: PyQt5/Tkinter (opcional)
- **API REST**: FastAPI con documentación automática

### 2. Capa de Negocio
- **Servicios**: Lógica de negocio (apuestas, bankroll, reportes)
- **Validadores**: Validación de datos con Pydantic
- **Gestores**: Gestión de transacciones y reglas de negocio

### 3. Capa de Datos
- **ORM**: SQLAlchemy
- **Modelos**: Entidades de base de datos
- **Repositorios**: Acceso a datos

## Componentes Principales

### Backend (FastAPI)
```
betcontrol/
├── app/
│   ├── api/              # Endpoints REST
│   ├── core/             # Configuración y seguridad
│   ├── models/           # Modelos SQLAlchemy
│   ├── schemas/          # Modelos Pydantic
│   ├── services/         # Lógica de negocio
│   ├── crud/             # Operaciones CRUD
│   ├── db/               # Configuración DB
│   └── utils/            # Utilidades
├── tests/                # Tests unitarios e integración
├── alembic/              # Migraciones de DB
└── docs/                 # Documentación
```

### Frontend (React)
```
frontend/
├── src/
│   ├── components/       # Componentes React
│   ├── pages/           # Páginas de la aplicación
│   ├── services/        # Servicios API
│   ├── hooks/           # Custom hooks
│   ├── utils/           # Utilidades
│   └── types/           # TypeScript types
└── public/              # Assets estáticos
```

## Flujo de Datos

1. **Registro de Apuesta**: Usuario → Frontend → API → Servicio → DB
2. **Actualización Bankroll**: Trigger automático en DB o lógica en servicio
3. **Reportes**: DB → Servicio → API → Frontend
4. **Análisis**: Queries optimizadas con índices apropiados

## Seguridad

- Autenticación JWT
- Validación de entrada con Pydantic
- SQL injection prevention con SQLAlchemy
- CORS configurado apropiadamente
- Rate limiting para prevenir abuso