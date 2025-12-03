import asyncio
import os
import sys
import logging
from datetime import datetime

# Add root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sync_job.log')
    ]
)
logger = logging.getLogger(__name__)

from app.db.session import SessionLocal
from app.services.ai_service import AIService
# Import models to ensure they are registered
import app.models

async def run_sync():
    """
    Main function to sync fixtures from API-Football to local DB.
    """
    logger.info("Starting daily fixture synchronization...")
    
    db = SessionLocal()
    service = AIService()
    
    try:
        # We call _sync_and_analyze directly if we want to force it, 
        # but get_daily_suggestions logic is "cache first".
        # To FORCE a sync (e.g. at midnight), we might want to call the internal method
        # or ensure the cache query returns nothing (which it will for a new day).
        
        # Using internal method _sync_and_analyze is safer for a dedicated sync script
        # as it bypasses the cache check.
        
        # However, since _sync_and_analyze is "private" by convention, 
        # we should ideally expose a public method. 
        # For now, we'll access it directly as we are the authors.
        
        suggestions = await service._sync_and_analyze(db)
        
        logger.info(f"Synchronization complete. Processed {len(suggestions)} top suggestions.")
        logger.info("Fixtures and statistics have been updated in the database.")
        
    except Exception as e:
        logger.error(f"Synchronization failed: {str(e)}")
        # Exit with error code for Task Scheduler to notice
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    # Run the async function
    asyncio.run(run_sync())
