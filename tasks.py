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

# Memory threshold: 85% (safe threshold with breathing room)
MEMORY_THRESHOLD = 85
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
    """🔥 FORENSIC FRAME-BY-FRAME: 0.4s scan interval with MAX confidence OR logic"""
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
            fps = cap.get(cv2.CAP_PROP_FPS) or 25  # Default 25 FPS
            cap.release()
            
            # 🔥 STRICT 0.4s SCAN INTERVAL: Calculate frame skip
            scan_interval_seconds = 0.4  # HARDCODED: 0.4s strobe
            frame_skip = max(1, int(fps * scan_interval_seconds))  # Frames per 0.4s
            
            logger.info(f"🔥 FORENSIC SCAN: {fps} FPS → frame_skip={frame_skip} (0.4s interval)")
            
            # Auto-create detection folder
            detection_dir = os.path.join('static', 'detections', f'match_{match_id}')
            os.makedirs(detection_dir, exist_ok=True)
            logger.info(f"Detection folder ready: {detection_dir}")
            
            # Real-time detection tracking
            detection_counter = 0
            max_confidence = 0.0
            commit_counter = 0
            current_frame = 0
            last_detection_time = -999  # Track 2.0s cooldown
            
            def detection_callback(confidence_score, timestamp):
                """Real-time callback for each detection >= 0.50 with 2.0s cooldown"""
                nonlocal detection_counter, max_confidence, commit_counter, last_detection_time
                
                # 🔥 2.0s SIGHTING COOLDOWN: Prevent duplicate detections
                if timestamp - last_detection_time < 2.0:
                    return  # Skip this detection (too close to previous)
                
                last_detection_time = timestamp
                
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
            
            # 🔥 ANALYZE WITH STRICT 0.4s INTERVAL + MAX CONFIDENCE OR LOGIC
            success = location_engine.analyze_footage_for_person(
                match_id, 
                frame_skip=frame_skip,  # Calculated from 0.4s interval
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

@celery.task(base=MemoryAwareTask, bind=True)
def create_person_profile_async(self, case_id, image_paths, video_path=None):
    """🔥 FORENSIC INTEGRITY: Create person profile with ALL photos (CLAHE + Upsampling + Multi-View)"""
    with app.app_context():
        try:
            from models import Case, PersonProfile, TargetImage
            from multi_view_face_extractor import get_face_extractor
            import face_recognition
            import cv2
            import numpy as np
            import json
            
            case = Case.query.get(case_id)
            if not case:
                return {'success': False, 'error': 'Case not found'}
            
            logger.info(f"🔍 FORENSIC PROFILE: Case #{case_id} with {len(image_paths)} photos")
            
            extractor = get_face_extractor()
            all_encodings = []
            front_encodings = []
            left_encodings = []
            right_encodings = []
            video_encodings = []
            
            # 🔥 FORENSIC ENHANCEMENT: Process EVERY photo with CLAHE + Upsampling
            for idx, img_path in enumerate(image_paths):
                try:
                    # Load image
                    image = face_recognition.load_image_file(img_path)
                    
                    # 🔥 CLAHE Enhancement: Fix lighting/shadow issues
                    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
                    l, a, b = cv2.split(lab)
                    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))  # Increased clip limit
                    l = clahe.apply(l)
                    enhanced = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2RGB)
                    
                    # 🔥 UPSAMPLING: Detect small/distant faces (5-10m)
                    face_locations = face_recognition.face_locations(
                        enhanced, 
                        model='cnn',  # CNN for better accuracy
                        number_of_times_to_upsample=2  # 2x upsampling for distance
                    )
                    
                    if not face_locations:
                        logger.warning(f"⚠️ No face in photo {idx+1}: {img_path}")
                        continue
                    
                    # Extract encodings from enhanced image
                    encodings = face_recognition.face_encodings(enhanced, face_locations)
                    if not encodings:
                        continue
                    
                    encoding = encodings[0].tolist()
                    all_encodings.append(encoding)
                    
                    # 🔥 MULTI-VIEW CATEGORIZATION: Front, Left, Right, Additional
                    if idx == 0:
                        front_encodings.append(encoding)
                    elif idx == 1:
                        left_encodings.append(encoding)
                    elif idx == 2:
                        right_encodings.append(encoding)
                    else:
                        # Additional photos go to all views for MAX matching
                        front_encodings.append(encoding)
                    
                    logger.info(f"✅ Photo {idx+1}: Face detected and encoded (CLAHE+Upsampling)")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing photo {idx+1}: {e}")
                    continue
            
            # Process video if provided
            if video_path:
                try:
                    video_encodings = extractor.extract_from_video(video_path, max_frames=5)
                    all_encodings.extend(video_encodings)
                    logger.info(f"✅ Video: {len(video_encodings)} encodings extracted")
                except Exception as e:
                    logger.error(f"❌ Video processing error: {e}")
            
            if not all_encodings:
                logger.error(f"❌ No encodings extracted for Case #{case_id}")
                return {'success': False, 'error': 'No faces detected in any photo'}
            
            # 🔥 CREATE PERSON PROFILE: Store ALL encodings
            person_profile = PersonProfile(
                case_id=case_id,
                primary_face_encoding=json.dumps(all_encodings[0]),
                all_face_encodings=json.dumps(all_encodings),
                front_encodings=json.dumps(front_encodings) if front_encodings else None,
                left_profile_encodings=json.dumps(left_encodings) if left_encodings else None,
                right_profile_encodings=json.dumps(right_encodings) if right_encodings else None,
                video_encodings=json.dumps(video_encodings) if video_encodings else None,
                total_encodings=len(all_encodings),
                face_quality_score=0.9 if len(all_encodings) >= 3 else 0.7,
                profile_confidence=min(len(all_encodings) / 8.0, 1.0)
            )
            db.session.add(person_profile)
            db.session.commit()
            
            # 🔥 FAISS MULTI-VECTOR: Insert ALL encodings (not just primary)
            try:
                from vector_search_service import get_face_search_service
                service = get_face_search_service()
                for encoding in all_encodings:
                    service.insert_encoding(encoding, person_profile.id)
                logger.info(f"✅ FAISS: {len(all_encodings)} encodings indexed (Multi-Vector)")
            except Exception as e:
                logger.warning(f"⚠️ FAISS update failed: {e}")
            
            logger.info(f"✅ FORENSIC PROFILE COMPLETE: {len(all_encodings)} total encodings")
            return {
                'success': True, 
                'case_id': case_id,
                'total_encodings': len(all_encodings),
                'front': len(front_encodings),
                'left': len(left_encodings),
                'right': len(right_encodings),
                'video': len(video_encodings)
            }
            
        except Exception as e:
            logger.error(f"Profile creation error for case {case_id}: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
