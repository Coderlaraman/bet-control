# Sistema de Control de Apuestas RushBet

Un sistema profesional y automatizado para controlar y analizar apuestas deportivas en la plataforma RushBet.

## 🚀 Características

### Gestión Completa de Apuestas
- ✅ Registro de apuestas simples y combinadas
- ✅ Control detallado con información de deporte, liga, mercado, evento
- ✅ Seguimiento de estado (pendiente, ganada, perdida, anulada)
- ✅ Cálculo automático de ganancias potenciales

### Control Automático de Bankroll
- ✅ Ajuste automático del bankroll al realizar apuestas
- ✅ Actualización automática según resultados
- ✅ Límites configurables (porcentaje máximo, montos mínimos/máximos)
- ✅ Historial completo de transacciones

### Análisis y Reportes Avanzados
- ✅ Estadísticas detalladas por deporte, liga, tipo de apuesta
- ✅ Análisis de ROI (Retorno de Inversión)
- ✅ Tasa de acierto (win rate)
- ✅ Gráficos y visualizaciones interactivas
- ✅ Dashboard con métricas clave
- ✅ Exportación de datos

### Seguridad y Autenticación
- ✅ Autenticación segura con JWT
- ✅ Gestión de usuarios con roles
- ✅ Protección de datos sensibles
- ✅ Cifrado de contraseñas con algoritmos seguros

## 🛠️ Stack Tecnológico

### Backend
- **Python 3.11+** - Lenguaje de programación
- **FastAPI 0.104.1** - Framework web moderno y rápido
- **SQLAlchemy 2.0.23** - ORM para base de datos
- **Pydantic** - Validación de datos
- **JWT** - Autenticación segura
- **Loguru** - Sistema de logging

### Frontend
- **React 18.2.0** - Framework de interfaz de usuario
- **TypeScript 5.3.2** - Tipado estático
- **Material-UI (MUI) 5.15.0** - Componentes de interfaz
- **React Router 6.20.1** - Enrutamiento
- **React Query** - Gestión de estado del servidor
- **Recharts 2.8.0** - Gráficos y visualizaciones

### Base de Datos
- **SQLite** - Para desarrollo
- **MySQL 8.0+** - Para producción

## 📋 Requisitos

### Sistema
- Python 3.11 o superior
- Node.js 18 o superior
- MySQL 8.0+ (para producción)

### Python Dependencies
```bash
pip install -r requirements.txt
```

### Node Dependencies
```bash
cd frontend && npm install
```

## 🚀 Instalación Rápida

### 1. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/betcontrol.git
cd betcontrol
```

### 2. Configurar Backend
```bash
# Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# Inicializar base de datos
python scripts/init_db.py

# Iniciar servidor de desarrollo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Configurar Frontend
```bash
cd frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm start
```

### 4. Acceder a la Aplicación
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs

## 📖 Documentación

### Documentación Completa
- [📋 Manual de Usuario](docs/manual_usuario.md) - Guía completa para usuarios
- [🔧 Documentación Técnica](docs/documentacion_tecnica.md) - Arquitectura y desarrollo
- [🚀 Guía de Despliegue](docs/guia_despliegue.md) - Despliegue en producción
- [🏗️ Arquitectura del Sistema](docs/arquitectura.md) - Diseño y arquitectura

### API Endpoints
- `POST /api/auth/register` - Registro de usuarios
- `POST /api/auth/login` - Inicio de sesión
- `GET /api/bets/` - Listar apuestas
- `POST /api/bets/` - Crear apuesta
- `GET /api/bankroll/summary` - Resumen de bankroll
- `GET /api/bets/stats` - Estadísticas

## 🧪 Testing

### Ejecutar Tests
```bash
# Todos los tests
python -m pytest tests/ -v

# Tests específicos
python -m pytest tests/test_bet_service.py -v
python -m pytest tests/test_bankroll_service.py -v

# Con coverage
coverage run -m pytest tests/
coverage report
coverage html
```

### Resultados de Tests
- ✅ 16 tests unitarios implementados
- ✅ Cobertura completa de servicios principales
- ✅ Tests de integración para flujos críticos

## 🔧 Configuración

### Variables de Entorno
```env
# Base de Datos
DB_HOST=localhost
DB_PORT=3306
DB_USER=betcontrol
DB_PASSWORD=tu_contraseña
DB_NAME=betcontrol

# Seguridad
SECRET_KEY=tu_clave_secreta_super_segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### Configuración de Bankroll
- **Porcentaje Máximo por Apuesta**: 5% (configurable)
- **Monto Mínimo**: $10 (configurable)
- **Monto Máximo**: $500 (configurable)
- **Moneda**: USD (configurable)

## 📊 Métricas y Análisis

### Estadísticas Disponibles
- **Total de Apuestas**: Número total de apuestas registradas
- **Tasa de Acierto**: Porcentaje de apuestas ganadas
- **ROI**: Retorno sobre inversión
- **Profit/Loss**: Ganancias o pérdidas netas
- **Distribución por Deporte**: Análisis por deporte
- **Distribución por Liga**: Análisis por liga
- **Evolución del Bankroll**: Gráfico temporal

### Reportes Generados
- Resumen general del rendimiento
- Análisis detallado por deporte/liga
- Historial de transacciones
- Exportación de datos en CSV/Excel

## 🔒 Seguridad

### Características de Seguridad
- ✅ Autenticación JWT con expiración
- ✅ Contraseñas hasheadas con pbkdf2_sha256
- ✅ Validación de entrada con Pydantic
- ✅ Protección CORS configurada
- ✅ Rate limiting (configurable)
- ✅ Logging de actividad sospechosa

### Mejores Prácticas de Seguridad
- Usar HTTPS en producción
- Mantener dependencias actualizadas
- Implementar rate limiting
- Monitorear logs de acceso
- Realizar backups regulares

## 🚀 Despliegue en Producción

### Usando Docker (Recomendado)
```bash
# Construir imágenes
docker-compose build

# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### Despliegue Manual
Ver [Guía de Despliegue](docs/guia_despliegue.md) para instrucciones detalladas.

## 📈 Monitoreo

### Métricas de Sistema
- Uso de CPU y memoria
- Espacio en disco
- Conexiones a base de datos
- Tiempo de respuesta de API

### Logs de Aplicación
- Logs de errores: `logs/error.log`
- Logs de aplicación: `logs/app.log`
- Logs de acceso: Configurable vía Nginx

## 🆘 Soporte

### Problemas Comunes
1. **Error de conexión a base de datos**: Verificar credenciales y conectividad
2. **Puerto ya en uso**: Cambiar puertos en configuración
3. **Error de autenticación**: Verificar token JWT y expiración
4. **Problemas de CORS**: Verificar configuración de orígenes permitidos

### Reportar Problemas
- Crear issue en GitHub
- Incluir logs de error relevantes
- Describir pasos para reproducir
- Incluir información del entorno

## 🤝 Contribuir

### Guía de Contribución
1. Fork el repositorio
2. Crear feature branch (`git checkout -b feature/amazing-feature`)
3. Commit cambios (`git commit -m 'Add amazing feature'`)
4. Push al branch (`git push origin feature/amazing-feature`)
5. Abrir Pull Request

### Estándares de Código
- Seguir PEP 8 para Python
- Seguir Airbnb Style Guide para JavaScript/TypeScript
- Escribir tests para nuevas funcionalidades
- Documentar código complejo

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

## 🙏 Agradecimientos

- FastAPI por el excelente framework
- React por la librería de UI
- SQLAlchemy por el ORM robusto
- Material-UI por los componentes de diseño
- Comunidad open source por las herramientas y librerías

## 📞 Contacto

**Desarrollador**: Tu Nombre
**Email**: tu.email@ejemplo.com
**LinkedIn**: [linkedin.com/in/tu-usuario](https://linkedin.com/in/tu-usuario)
**GitHub**: [@tu-usuario](https://github.com/tu-usuario)

---

**⚠️ Advertencia**: Este sistema es una herramienta de análisis y gestión de apuestas. No garantiza ganancias y debe usarse de forma responsable. Apuesta solo lo que puedas permitirte perder.