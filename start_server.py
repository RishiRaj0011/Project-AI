import os
import sys
import logging
from __init__ import create_app, db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    app = create_app()
    
    with app.app_context():
        db.create_all()
        logger.info("Database ready")
    
    logger.info("=" * 60)
    logger.info("Missing Person Investigation System - RUNNING")
    logger.info("=" * 60)
    logger.info("URL: http://localhost:5000")
    logger.info("Admin: admin / admin123")
    logger.info("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
