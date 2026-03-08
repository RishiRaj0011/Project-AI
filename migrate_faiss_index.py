"""
FAISS Index Migration Script
Rebuilds the FAISS index from database PersonProfile records
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from __init__ import create_app, db
from models import PersonProfile
from vector_search_service import get_face_search_service
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_faiss_index():
    """Migrate FAISS index to new IVF implementation"""
    app = create_app()
    
    with app.app_context():
        logger.info("="*60)
        logger.info("FAISS Index Rebuild - IndexFlatIP")
        logger.info("="*60)
        
        try:
            # Get all person profiles
            logger.info("Fetching person profiles from database...")
            profiles = PersonProfile.query.all()
            logger.info(f"Found {len(profiles)} person profiles")
            
            if len(profiles) == 0:
                logger.warning("No person profiles found. Nothing to migrate.")
                # Check for approved cases
                from models import Case
                approved_cases = Case.query.filter(Case.status.in_(['Approved', 'Under Processing'])).all()
                logger.info(f"Debug: Found {len(approved_cases)} Approved/Under Processing cases")
                if len(approved_cases) == 0:
                    logger.warning("No Approved/Under Processing cases found in database")
                else:
                    logger.warning("Approved cases exist but no PersonProfile records found")
                return
            
            # Get FAISS service
            logger.info("Initializing FAISS service...")
            service = get_face_search_service()
            
            # Rebuild index
            logger.info("Rebuilding FAISS index...")
            service.rebuild_from_database(profiles)
            
            # Verify
            index_size = service.get_index_size()
            logger.info(f"✅ Rebuild complete! Index size: {index_size} encodings")
            
            logger.info("="*60)
            logger.info("Rebuild successful!")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"❌ Rebuild failed: {str(e)}")
            logger.error("Please check the error and try again")
            raise

if __name__ == "__main__":
    logger.info("Starting FAISS index rebuild...")
    migrate_faiss_index()
    logger.info("Rebuild script completed")
