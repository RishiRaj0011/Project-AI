# Suppress warnings
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="face_recognition_models")
warnings.filterwarnings("ignore", message=".*pkg_resources is deprecated.*")
warnings.filterwarnings("ignore", message=".*ComplexWarning.*")

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError, DatabaseError
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_moment import Moment
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO
from celery import Celery
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
bcrypt = Bcrypt()
moment = Moment()
csrf = CSRFProtect()
socketio = SocketIO()

def make_celery(app):
    broker_url = app.config.get("CELERY_BROKER_URL") or "sqla+sqlite:///celery.db"
    result_backend = app.config.get("result_backend") or app.config.get("CELERY_RESULT_BACKEND") or "db+sqlite:///celery_results.db"
    
    celery = Celery(app.import_name, backend=result_backend, broker=broker_url)
    celery.conf.update({
        'result_backend': result_backend,
        'broker_url': broker_url,
        'broker_connection_retry_on_startup': True,
        **{k: v for k, v in app.config.items() if not k.startswith('CELERY_')}
    })
    return celery

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    login.login_view = "main.login"
    login.login_message = "Please log in to access this page"
    bcrypt.init_app(app)
    moment.init_app(app)
    csrf.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Initialize AI services
    with app.app_context():
        try:
            from vector_search_service import get_face_search_service
            service = get_face_search_service()
            print(f"✅ FAISS: {service.get_index_size()} encodings")
        except Exception as e:
            print(f"⚠️ FAISS: {e}")
        
        try:
            from automated_cleanup_service import AutomatedCleanupService
            AutomatedCleanupService().run_startup_cleanup()
            print(f"✅ Cleanup: Completed")
        except Exception as e:
            print(f"⚠️ Cleanup: {e}")
    
    # CSRF exemptions
    csrf.exempt('learning.record_admin_feedback')
    csrf.exempt('learning.trigger_learning')
    csrf.exempt('learning.reduce_false_positives')
    csrf.exempt('learning.update_threshold')
    
    # Track user activity
    @app.before_request
    def track_user_activity():
        from flask_login import current_user
        from models import get_ist_now
        
        if current_user.is_authenticated:
            current_time = get_ist_now()
            if not hasattr(current_user, '_last_activity_update') or \
               (current_time - current_user._last_activity_update).seconds > 300:
                current_user.last_seen = current_time
                current_user.is_online = True
                current_user._last_activity_update = current_time
                try:
                    db.session.commit()
                except (SQLAlchemyError, DatabaseError):
                    try:
                        db.session.rollback()
                    except (SQLAlchemyError, DatabaseError):
                        pass
    
    # Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: https:; script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; style-src 'self' 'unsafe-inline' https:; font-src 'self' https:; img-src 'self' data: blob: https:; connect-src 'self' https:;"
        return response

    from routes import bp as main_bp
    from error_handlers import register_error_handlers
    app.register_blueprint(main_bp)
    
    # Register blueprints with proper error handling
    blueprints = [
        ('admin', 'admin_bp'),
        ('continuous_learning_routes', 'learning_bp'),
        ('location_matching_routes', 'location_bp'),
        ('enhanced_admin_routes', 'enhanced_admin_bp')
    ]
    
    for module_name, bp_name in blueprints:
        try:
            module = __import__(module_name)
            app.register_blueprint(getattr(module, bp_name))
            print(f"✅ Blueprint: {bp_name}")
        except Exception as e:
            print(f"⚠️ Blueprint {bp_name}: {e}")
    
    register_error_handlers(app)
    
    # Template helpers
    from template_helpers import get_image_url, get_primary_photo_url, get_video_url, verify_file_exists
    from status_helpers import get_status_display_info, get_status_badge_html, get_status_alert_html
    from status_template_helpers import (
        status_badge_filter, status_icon_filter, status_emoji_filter, status_color_filter,
        get_status_card_html, get_status_progress_html, get_status_summary_stats
    )
    from comprehensive_status_system import ALL_CASE_STATUSES, PUBLIC_VISIBLE_STATUSES, ACTIVE_STATUSES
    
    app.template_filter('image_url')(get_image_url)
    app.template_filter('video_url')(get_video_url)
    app.template_global()(lambda case: get_primary_photo_url(case))
    app.template_global('file_exists')(verify_file_exists)
    app.template_global('get_status_info')(get_status_display_info)
    app.template_filter('status_badge')(status_badge_filter)
    app.template_filter('status_icon')(status_icon_filter)
    app.template_filter('status_emoji')(status_emoji_filter)
    app.template_filter('status_color')(status_color_filter)
    app.template_filter('status_alert')(get_status_alert_html)
    
    @app.template_filter('days_since')
    def days_since_filter(date_obj):
        if not date_obj:
            return 0
        from datetime import datetime
        try:
            now = datetime.utcnow()
            delta = now - (date_obj if date_obj.tzinfo is None else datetime.utcfromtimestamp(date_obj.timestamp()))
            return max(0, delta.days)
        except:
            return 0
    
    app.template_global('get_all_statuses')(lambda: ALL_CASE_STATUSES)
    app.template_global('get_public_statuses')(lambda: PUBLIC_VISIBLE_STATUSES)
    app.template_global('get_active_statuses')(lambda: ACTIVE_STATUSES)
    app.template_global('get_status_card')(get_status_card_html)
    app.template_global('get_status_progress')(get_status_progress_html)
    app.template_global('get_status_stats')(get_status_summary_stats)
    
    # Context processor
    @app.context_processor
    def inject_global_data():
        from flask_login import current_user
        from models import Announcement, Notification, get_ist_now, AnnouncementRead
        
        active_announcements = []
        unread_count = 0
        
        if current_user.is_authenticated:
            try:
                current_time = get_ist_now()
                all_active = Announcement.query.filter(
                    Announcement.is_active == True,
                    db.or_(Announcement.expires_at == None, Announcement.expires_at > current_time)
                ).order_by(Announcement.created_at.desc()).all()
                
                read_ids = [r[0] for r in db.session.query(AnnouncementRead.announcement_id).filter_by(user_id=current_user.id).all()]
                active_announcements = [a for a in all_active if a.id not in read_ids]
            except:
                pass
            
            unread_count = current_user.unread_notifications_count
        
        return {'active_announcements': active_announcements, 'unread_notifications_count': unread_count}

    return app

@login.user_loader
def load_user(user_id):
    from models import User
    try:
        return User.query.get(int(user_id))
    except (ValueError, TypeError):
        return None

import models
