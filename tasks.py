"""
Celery Tasks - Scalable Video Processing with Memory Management
NO THREADING FALLBACK - Celery only
"""
import psutil
import time
import traceback
import sys
from celery import Task
from celery_app import celery, app
from __init__ import db
from models import LocationMatch, Case
import logging

logger = logging.getLogger(__name__)

# Memory threshold: 98% (relaxed for high baseline usage)
MEMORY_THRESHOLD = 98
MAX_CONCURRENT_VIDEOS = 4

class MemoryAwareTask(Task):
    """Base task with memory checking"""
    def before_start(self, task_id, args, kwargs):
        """Check memory before starting"""
        while psutil.virtual_memory().percent > MEMORY_THRESHOLD:
            logger.warning(f"Memory at {psutil.virtual_memory().percent}% - pausing queue")
            time.sleep(10)

@celery.task(base=MemoryAwareTask, bind=True, max_retries=3)
def analyze_footage_match(self, match_id):
    """FORENSIC FRAME-BY-FRAME: Analyze single footage match with REAL-TIME progress tracking"""
    with app.app_context():
        match = None
        try:
            import os
            from location_matching_engine import location_engine
            from datetime import datetime
            import cv2
            
            match = LocationMatch.query.get(match_id)
            if not match:
                return {'success': False, 'error': 'Match not found'}
            
            # IMMEDIATE STATUS UPDATE
            match.status = 'processing'
            match.ai_analysis_started = datetime.utcnow()
            match.detection_count = 0
            match.confidence_score = 0.0
            match.person_found = False
            db.session.commit()
            
            # Get total frames for progress calculation
            footage_path = os.path.join('static', match.footage.video_path)
            if not os.path.exists(footage_path):
                footage_path = os.path.join('app', 'static', match.footage.video_path)
            
            cap = cv2.VideoCapture(footage_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            
            # Auto-create detection folder
            detection_dir = os.path.join('static', 'detections', f'match_{match_id}')
            os.makedirs(detection_dir, exist_ok=True)
            logger.info(f"Detection folder ready: {detection_dir}")
            
            # HARDCODED: frame_skip=1 for forensic accuracy
            frame_skip = 1
            
            # Real-time detection tracking
            detection_counter = 0
            max_confidence = 0.0
            commit_counter = 0
            current_frame = 0
            
            def detection_callback(confidence_score):
                """Real-time callback for each detection >= 0.50"""
                nonlocal detection_counter, max_confidence, commit_counter
                
                # Immediate counter increment
                detection_counter += 1
                max_confidence = max(max_confidence, confidence_score)
                
                # Update match record immediately
                match.detection_count = detection_counter
                match.confidence_score = max_confidence
                match.person_found = True
                
                # Commit every 5 detections for real-time dashboard updates
                commit_counter += 1
                if commit_counter % 5 == 0:
                    db.session.commit()
                    logger.info(f"✅ Real-time sync: {detection_counter} detections, max confidence: {max_confidence:.3f}")
            
            def progress_callback(frame_num):
                """Progress callback for Celery state updates every 10 frames"""
                nonlocal current_frame
                current_frame = frame_num
                
                if total_frames > 0:
                    percent = int((current_frame / total_frames) * 100)
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'percent': percent,
                            'current_frame': current_frame,
                            'total_frames': total_frames,
                            'detections': detection_counter,
                            'max_confidence': max_confidence,
                            'status': 'processing'
                        }
                    )
            
            # Analyze with real-time callbacks (frame_skip=1 hardcoded)
            success = location_engine.analyze_footage_for_person(
                match_id, 
                frame_skip=frame_skip,
                snapshot_interval=30,
                detection_callback=detection_callback,
                progress_callback=progress_callback
            )
            
            # Final database update
            match.detection_count = detection_counter
            match.confidence_score = max_confidence
            match.person_found = detection_counter > 0
            match.status = 'completed'
            match.ai_analysis_completed = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"✅ Analysis complete: Match {match_id}, {detection_counter} detections, max confidence: {max_confidence:.3f}")
            
            return {'success': success, 'match_id': match_id, 'detections': detection_counter}
            
        except Exception as e:
            print(f"DEBUG: Error at line {traceback.extract_tb(sys.exc_info()[2])[-1][1]} in {traceback.extract_tb(sys.exc_info()[2])[-1][0]}")
            logger.error(f"Task error for match {match_id}: {e}")
            traceback.print_exc()
            if match:
                match.status = 'failed'
                db.session.commit()
            raise self.retry(exc=e, countdown=60)
        
        finally:
            # COMPLETION GUARD: Ensure status is NEVER left as 'processing'
            if match:
                try:
                    # Refresh match from database
                    match = LocationMatch.query.get(match_id)
                    if match and match.status == 'processing':
                        from datetime import datetime
                        
                        match.status = 'completed'
                        match.person_found = match.detection_count > 0
                        match.ai_analysis_completed = datetime.utcnow()
                        db.session.commit()
                        
                        logger.info(f"✅ COMPLETION GUARD: Match {match_id} completed with {match.detection_count} detections")
                        
                except Exception as final_error:
                    logger.error(f"❌ COMPLETION GUARD ERROR: {final_error}")
                    try:
                        db.session.rollback()
                    except:
                        pass

@celery.task(base=MemoryAwareTask, bind=True)
def analyze_batch_parallel(self, case_id, footage_ids, batch_id):
    """Batch analysis with strict concurrency limit"""
    with app.app_context():
        try:
            from location_matching_engine import location_engine
            
            results = []
            for footage_id in footage_ids:
                # Check memory before each video
                if psutil.virtual_memory().percent > MEMORY_THRESHOLD:
                    logger.warning(f"Memory at {psutil.virtual_memory().percent}% - pausing")
                    time.sleep(30)
                
                match = LocationMatch.query.filter_by(
                    case_id=case_id,
                    footage_id=footage_id,
                    batch_id=batch_id
                ).first()
                
                if match:
                    match.status = 'processing'
                    db.session.commit()
                    
                    success = location_engine.analyze_footage_for_person(match.id)
                    results.append({'footage_id': footage_id, 'success': success})
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            logger.error(f"Batch analysis error: {e}")
            return {'success': False, 'error': str(e)}

@celery.task(base=MemoryAwareTask, bind=True)
def process_batch_with_progress(self, case_id, footage_ids, batch_id):
    """Batch processing with progress updates"""
    with app.app_context():
        try:
            from location_matching_engine import location_engine
            
            total = len(footage_ids)
            for idx, footage_id in enumerate(footage_ids):
                # Memory check
                if psutil.virtual_memory().percent > MEMORY_THRESHOLD:
                    logger.warning(f"Memory at {psutil.virtual_memory().percent}% - waiting")
                    time.sleep(30)
                
                # Update progress
                self.update_state(
                    state='PROGRESS',
                    meta={'current': idx + 1, 'total': total, 'percent': int((idx + 1) / total * 100)}
                )
                
                success = location_engine.analyze_with_progress(
                    case_id, footage_id, batch_id
                )
            
            return {'success': True, 'total': total}
            
        except Exception as e:
            logger.error(f"Progress batch error: {e}")
            return {'success': False, 'error': str(e)}

@celery.task(base=MemoryAwareTask, bind=True)
def process_footage_high_precision(self, case_id, footage_id, batch_id):
    """High-precision forensic analysis (0.88 threshold)"""
    with app.app_context():
        try:
            from location_matching_engine import location_engine
            
            # Check memory
            if psutil.virtual_memory().percent > MEMORY_THRESHOLD:
                logger.warning(f"Memory at {psutil.virtual_memory().percent}% - delaying")
                time.sleep(30)
            
            match = LocationMatch.query.filter_by(
                case_id=case_id,
                footage_id=footage_id,
                batch_id=batch_id
            ).first()
            
            if not match:
                match = LocationMatch(
                    case_id=case_id,
                    footage_id=footage_id,
                    batch_id=batch_id,
                    status='processing',
                    match_type='high_precision'
                )
                db.session.add(match)
                db.session.commit()
            
            # Use strict 0.88 threshold
            success = location_engine.analyze_footage_for_person(match.id)
            
            return {'success': success, 'footage_id': footage_id}
            
        except Exception as e:
            logger.error(f"HP analysis error: {e}")
            return {'success': False, 'error': str(e)}

@celery.task(base=MemoryAwareTask, bind=True)
def process_batch_high_precision(self, case_id, footage_ids, batch_id):
    """Batch high-precision analysis with memory management"""
    with app.app_context():
        try:
            results = []
            for footage_id in footage_ids:
                # Strict memory check
                while psutil.virtual_memory().percent > MEMORY_THRESHOLD:
                    logger.warning(f"Memory at {psutil.virtual_memory().percent}% - paused")
                    time.sleep(30)
                
                result = process_footage_high_precision(case_id, footage_id, batch_id)
                results.append(result)
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            logger.error(f"HP batch error: {e}")
            return {'success': False, 'error': str(e)}

@celery.task(base=MemoryAwareTask, bind=True)
def process_case_media(self, case_id):
    """Process case media after re-queue - creates matches and starts analysis"""
    with app.app_context():
        try:
            from location_matching_engine import location_engine
            from models import Case, LocationMatch
            
            case = Case.query.get(case_id)
            if not case:
                return {'success': False, 'error': 'Case not found'}
            
            logger.info(f"⚙️ Processing case media for Case #{case_id}")
            
            # Create location matches
            matches_created = location_engine.process_new_case(case_id)
            
            if matches_created > 0:
                # Start analysis for all pending matches
                pending_matches = LocationMatch.query.filter_by(
                    case_id=case_id,
                    status='pending'
                ).all()
                
                for match in pending_matches:
                    analyze_footage_match.delay(match.id)
                
                # Update case status
                case.status = 'Under Processing'
                db.session.commit()
                
                logger.info(f"✅ Case #{case_id} processing started: {matches_created} matches, {len(pending_matches)} analyses queued")
                return {'success': True, 'matches': matches_created, 'analyses': len(pending_matches)}
            else:
                logger.warning(f"⚠️ Case #{case_id}: No footage matches found")
                return {'success': True, 'matches': 0, 'message': 'No matching footage found'}
                
        except Exception as e:
            logger.error(f"Error processing case media {case_id}: {e}")
            return {'success': False, 'error': str(e)}
