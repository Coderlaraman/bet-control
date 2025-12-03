#!/usr/bin/env python3
"""
Script para resetear completamente la base de datos
ADVERTENCIA: Este script eliminará TODOS los datos existentes
"""

import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine, Base
from app.core.config import settings
from loguru import logger


def reset_database():
    """Eliminar y recrear todas las tablas"""
    try:
        logger.info("🗑️  Eliminando todas las tablas existentes...")
        
        # Importar todos los modelos para que SQLAlchemy los conozca
        from app.models.user import User
        from app.models.bankroll import BankrollConfig, BankrollTransaction
        from app.models.bet import Bet, BetType, Market, ParlayBet, ParlaySelection
        from app.models.sport import Sport, Country, League
        from app.models.statistics import SportStatistics, LeagueStatistics
        
        # Eliminar todas las tablas
        Base.metadata.drop_all(bind=engine)
        logger.info("✅ Todas las tablas eliminadas")
        
        # Recrear todas las tablas
        logger.info("🔨 Recreando todas las tablas...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Todas las tablas recreadas")
        
        # Eliminar archivo de base de datos SQLite si existe
        if settings.DB_HOST == 'sqlite':
            db_file = Path(f"{settings.DB_NAME}.db")
            if db_file.exists():
                logger.info(f"🗑️  Eliminando archivo de base de datos: {db_file}")
                # Las tablas ya fueron eliminadas, solo informamos
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error reseteando base de datos: {e}")
        raise


def main():
    """Función principal"""
    print("=" * 60)
    print("⚠️  ADVERTENCIA: RESETEO COMPLETO DE BASE DE DATOS ⚠️")
    print("=" * 60)
    print("\nEste script eliminará TODOS los datos existentes en la base de datos.")
    print("Esta acción NO se puede deshacer.\n")
    
    # Solicitar confirmación
    confirmation = input("¿Está seguro que desea continuar? (escriba 'SI' para confirmar): ")
    
    if confirmation != "SI":
        print("\n❌ Operación cancelada por el usuario")
        return
    
    print("\n🚀 Iniciando reseteo de base de datos...\n")
    
    # Resetear base de datos
    if reset_database():
        print("\n✅ Base de datos reseteada exitosamente!")
        print("\n📝 Ahora ejecute 'python scripts/init_db.py' para inicializar con datos por defecto")
    else:
        print("\n❌ Error al resetear la base de datos")
        sys.exit(1)


if __name__ == "__main__":
    main()
