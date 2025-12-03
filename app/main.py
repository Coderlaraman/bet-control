from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import time
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.api.v1.router import api_router
from app.db.session import init_db, check_db_connection, SessionLocal
from app.services.ai_service import AIService

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sistema profesional de control de apuestas para RushBet",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Scheduler instance
scheduler = AsyncIOScheduler()

async def scheduled_sync():
    """Function to run daily sync via scheduler"""
    logger.info("Executing scheduled daily sync...")
    try:
        db = SessionLocal()
        service = AIService()
        # Using internal method to force sync
        await service._sync_and_analyze(db)
        db.close()
        logger.info("Scheduled sync completed successfully")
    except Exception as e:
        logger.error(f"Scheduled sync failed: {e}")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Middleware para medir tiempo de respuesta"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logging de requests"""
    start_time = time.time()
    
    # Log del request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    # Log de la respuesta
    process_time = time.time() - start_time
    logger.info(
        f"Response: {response.status_code} "
        f"for {request.method} {request.url.path} "
        f"in {process_time:.4f}s"
    )
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Manejador global de excepciones"""
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "details": None
        }
    )


@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Verificar conexión a base de datos
    if not check_db_connection():
        logger.error("Database connection failed")
        raise Exception("Cannot connect to database")
    
    # Inicializar base de datos
    init_db()
    
    # Start Scheduler
    try:
        # Schedule job to run at 00:05 AM every day
        trigger = CronTrigger(hour=0, minute=5, timezone="UTC") 
        scheduler.add_job(scheduled_sync, trigger)
        scheduler.start()
        logger.info("Scheduler started: Daily sync set for 00:05 UTC")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")

    logger.info("Application started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre de la aplicación"""
    logger.info("Shutting down application")


# Incluir routers
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/api/docs"
    }


@app.get("/health")
async def health_check():
    """Endpoint de salud"""
    return {
        "status": "healthy",
        "database": "connected" if check_db_connection() else "disconnected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8075,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )