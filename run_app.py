"""
Proper Flask Application Runner
Production-grade with automated startup checks
"""
import sys
import os
import site
import logging
from __init__ import create_app, db

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_database(app_instance):
    """Initialize database within app context"""
    with app_instance.app_context():
        try:
            from models import User
            db.create_all()
            
            # Ensure default admin exists
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(username='admin', email='admin@example.com', is_admin=True)
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                logger.info("Default admin user created")
            
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")

def startup_checks(app_instance):
    """Run comprehensive startup checks"""
    with app_instance.app_context():
        logger.info("Running startup checks...")
        
        # Check FAISS index
        try:
            from vector_search_service import get_face_search_service
            service = get_face_search_service()
            index_size = service.get_index_size()
            logger.info(f"✅ FAISS: {index_size} face encodings indexed")
            
            # Debug FAISS if 0 encodings
            if index_size == 0:
                from models import Case, PersonProfile
                approved_cases = Case.query.filter(Case.status.in_(['Approved', 'Under Processing'])).count()
                person_profiles = PersonProfile.query.count()
                logger.warning(f"🔍 FAISS Debug: {approved_cases} Approved/Under Processing cases, {person_profiles} PersonProfile records")
                if approved_cases == 0:
                    logger.warning("❌ No Approved/Under Processing cases found in database - FAISS has nothing to index")
                elif person_profiles == 0:
                    logger.warning("❌ No PersonProfile records found - face encodings missing")
                    logger.info("🔄 Auto-fixing: Running PersonProfile rebuild...")
                    try:
                        from rebuild_profiles import rebuild_missing_profiles
                        profiles_created = rebuild_missing_profiles()
                        if profiles_created > 0:
                            logger.info(f"✅ Auto-fix complete: {profiles_created} profiles created")
                        else:
                            logger.warning("⚠️ Auto-fix: No profiles could be created - check case images")
                    except Exception as e:
                        logger.error(f"❌ Auto-fix failed: {e}")
                else:
                    logger.warning("❌ PersonProfile records exist but no face encodings - check face_encoding field")
        except Exception as e:
            logger.warning(f"⚠️ FAISS check failed: {e}")
        
        # Check vision engine
        try:
            from vision_engine import get_vision_engine
            engine = get_vision_engine()
            logger.info(f"✅ Vision engine: Ready")
        except Exception as e:
            logger.warning(f"⚠️ Vision engine check failed: {e}")
        
        # Run automated cleanup
        try:
            from automated_cleanup_service import AutomatedCleanupService
            cleanup = AutomatedCleanupService()
            cleanup.run_startup_cleanup()
            logger.info(f"✅ Automated cleanup: Completed")
        except Exception as e:
            logger.warning(f"⚠️ Cleanup failed: {e}")
        
        logger.info("Startup checks completed")

def main():
    """Main application runner"""
    app = create_app()
    
    logger.info("="*60)
    logger.info("Starting Flask Application - Production Mode")
    logger.info("="*60)
    logger.info("Access URL: http://localhost:5000")
    logger.info("Admin credentials: admin / admin123")
    logger.info("="*60)
    
    # Safe debug mode control
    is_debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1', 't']
    
    if is_debug:
        logger.warning("⚠️ Running in DEBUG MODE - not for production")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=is_debug
    )

if __name__ == "__main__":
    app = create_app()
    setup_database(app)
    startup_checks(app)
    main()