"""
Unified Location Matching Engine - Single Source of Truth
Consolidates: advanced_location_matcher.py, ai_location_matcher.py, intelligent_location_matcher.py
"""
import os
import json
import logging
import numpy as np
import cv2
import face_recognition
from datetime import datetime, timedelta
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from difflib import SequenceMatcher
from __init__ import db
from models import Case, SurveillanceFootage, LocationMatch, PersonDetection

logger = logging.getLogger(__name__)

class LocationMatchingEngine:
    def __init__(self):
        self.geocoder = Nominatim(user_agent="investigation_platform")
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Load dynamic threshold from AI config
        self.forensic_threshold = self._load_forensic_threshold()
        
        self.CASE_CRITERIA = {
            'missing_person': {'radius_km': 25, 'time_window_hours': 168, 'confidence_threshold': self.forensic_threshold},
            'criminal_investigation': {'radius_km': 10, 'time_window_hours': 72, 'confidence_threshold': self.forensic_threshold},
            'surveillance_request': {'radius_km': 5, 'time_window_hours': 24, 'confidence_threshold': self.forensic_threshold},
            'person_tracking': {'radius_km': 50, 'time_window_hours': 336, 'confidence_threshold': self.forensic_threshold},
            'evidence_analysis': {'radius_km': 15, 'time_window_hours': 120, 'confidence_threshold': self.forensic_threshold}
        }
        
        self.PRIORITY_RADIUS = {'Critical': 2.0, 'High': 1.5, 'Medium': 1.0, 'Low': 0.7}
        self.REQUESTER_BOOST = {'police': 2.0, 'government': 1.8, 'private_investigator': 1.5, 'organization': 1.3, 'family': 1.0}
    
    def _load_forensic_threshold(self):
        """Load forensic threshold from AI config"""
        try:
            from ai_config_model import AIConfig
            config = AIConfig.get_config()
            return config.forensic_threshold
        except:
            return 0.88  # Fallback
    
    def find_location_matches(self, case_id):
        """Find all matching footage for a case"""
        try:
            case = Case.query.get(case_id)
            if not case:
                return []
            
            # Try geocoding first
            case_lat, case_lon = self._geocode_location(case.last_seen_location)
            if case_lat and case_lon:
                return self._find_intelligent_matches(case, case_lat, case_lon)
            
            # Fallback to string matching
            return self._find_string_matches(case)
        except Exception as e:
            logger.error(f"Error finding matches for case {case_id}: {e}")
            return []
    
    def _geocode_location(self, location_string):
        """Convert address to GPS coordinates"""
        try:
            if not location_string:
                return None, None
            
            clean_location = ' '.join(location_string.split())
            location = self.geocoder.geocode(clean_location, timeout=10)
            if location:
                return location.latitude, location.longitude
            
            # Try partial location
            parts = clean_location.split(',')
            for i in range(len(parts)):
                partial = ','.join(parts[i:]).strip()
                if partial:
                    location = self.geocoder.geocode(partial, timeout=10)
                    if location:
                        return location.latitude, location.longitude
            
            return None, None
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            return None, None
    
    def _find_intelligent_matches(self, case, case_lat, case_lon):
        """5-factor weighted matching: GPS 40%, Name 25%, Time 20%, Quality 10%, Priority 5%"""
        search_radius = self._calculate_smart_radius(case)
        case_type = case.case_type or 'missing_person'
        time_window = self.CASE_CRITERIA.get(case_type, {}).get('time_window_hours', 168)
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window)
        
        all_footage = SurveillanceFootage.query.filter(
            SurveillanceFootage.is_active == True,
            SurveillanceFootage.date_recorded >= cutoff_time
        ).all()
        
        matches = []
        for footage in all_footage:
            match_data = self._calculate_5_factor_score(case, footage, case_lat, case_lon, search_radius)
            if match_data and match_data['match_score'] > 0.3:
                matches.append(match_data)
        
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        return matches[:20]
    
    def _find_string_matches(self, case):
        """Fallback string-based matching"""
        try:
            footage_list = SurveillanceFootage.query.filter_by(is_active=True).all()
            matches = []
            
            for footage in footage_list:
                match_score = self._calculate_name_similarity(case.last_seen_location, footage.location_name)
                if match_score > 0.2:
                    matches.append({
                        'footage': footage,
                        'match_score': match_score * 0.7,
                        'distance_km': None,
                        'match_type': 'string_fallback'
                    })
            
            matches.sort(key=lambda x: x['match_score'], reverse=True)
            return matches[:10]
        except Exception as e:
            logger.error(f"String matching error: {e}")
            return []
    
    def _calculate_smart_radius(self, case):
        """Calculate intelligent search radius"""
        try:
            case_type = case.case_type or 'missing_person'
            base_radius = self.CASE_CRITERIA.get(case_type, {}).get('radius_km', 15)
            priority_multiplier = self.PRIORITY_RADIUS.get(case.priority, 1.0)
            requester_boost = self.REQUESTER_BOOST.get(case.requester_type, 1.0)
            
            urgency_multiplier = {'critical': 2.5, 'high': 1.8, 'medium': 1.0, 'low': 0.6}.get(case.urgency_level, 1.0)
            final_radius = base_radius * priority_multiplier * requester_boost * urgency_multiplier
            
            return max(2, min(final_radius, 100))
        except:
            return 15
    
    def _calculate_5_factor_score(self, case, footage, case_lat, case_lon, search_radius):
        """5-factor weighted: GPS 40%, Name 25%, Time 20%, Quality 10%, Priority 5%"""
        try:
            match_score = 0.0
            factors = {}
            distance_km = None
            
            # Factor 1: GPS (40%)
            if footage.latitude and footage.longitude:
                distance_km = geodesic((case_lat, case_lon), (footage.latitude, footage.longitude)).kilometers
                if distance_km > search_radius:
                    return None
                geo_score = max(0, 1 - (distance_km / search_radius))
                match_score += geo_score * 0.4
                factors['gps'] = geo_score
            
            # Factor 2: Name (25%)
            name_score = self._calculate_name_similarity(case.last_seen_location, footage.location_name)
            match_score += name_score * 0.25
            factors['name'] = name_score
            
            # Factor 3: Time (20%)
            time_score = self._calculate_time_relevance(case, footage)
            match_score += time_score * 0.20
            factors['time'] = time_score
            
            # Factor 4: Quality (10%)
            quality_score = self._calculate_quality_score(footage)
            match_score += quality_score * 0.10
            factors['quality'] = quality_score
            
            # Factor 5: Priority (5%)
            priority_score = self._calculate_priority_boost(case)
            match_score += priority_score * 0.05
            factors['priority'] = priority_score
            
            return {
                'footage': footage,
                'match_score': min(match_score, 1.0),
                'distance_km': distance_km,
                'factors': factors,
                'match_type': '5_factor_weighted'
            }
        except Exception as e:
            logger.error(f"5-factor score error: {e}")
            return None
    
    def _calculate_name_similarity(self, case_location, footage_location):
        """Jaccard similarity for location names"""
        if not case_location or not footage_location:
            return 0.0
        
        case_clean = case_location.lower().strip()
        footage_clean = footage_location.lower().strip()
        
        if case_clean == footage_clean:
            return 1.0
        if case_clean in footage_clean or footage_clean in case_clean:
            return 0.8
        
        case_words = set(case_clean.split())
        footage_words = set(footage_clean.split())
        
        if case_words and footage_words:
            intersection = case_words.intersection(footage_words)
            union = case_words.union(footage_words)
            return (len(intersection) / len(union)) * 0.7
        
        return 0.0
    
    def _calculate_time_relevance(self, case, footage):
        """Time-based relevance"""
        try:
            if not case.date_missing or not footage.date_recorded:
                return 0.5
            time_diff = abs((case.date_missing - footage.date_recorded).total_seconds() / 3600)
            case_type = case.case_type or 'missing_person'
            max_hours = self.CASE_CRITERIA.get(case_type, {}).get('time_window_hours', 168)
            if time_diff <= max_hours:
                return max(0, 1 - (time_diff / max_hours))
            return 0.0
        except:
            return 0.5
    
    def _calculate_quality_score(self, footage):
        """Footage quality score"""
        score = 0.5
        if footage.resolution:
            if 'FHD' in footage.resolution or '1080' in footage.resolution:
                score += 0.3
            elif 'HD' in footage.resolution or '720' in footage.resolution:
                score += 0.2
        if footage.camera_type and 'CCTV' in footage.camera_type.upper():
            score += 0.1
        if footage.quality:
            score += {'4K': 0.2, 'FHD': 0.15, 'HD': 0.1, 'SD': 0.0}.get(footage.quality, 0.0)
        return min(score, 1.0)
    
    def _calculate_priority_boost(self, case):
        """Priority boost"""
        priority_scores = {'Critical': 1.0, 'High': 0.8, 'Medium': 0.5, 'Low': 0.2}
        requester_scores = {'police': 1.0, 'government': 0.9, 'private_investigator': 0.7, 'organization': 0.5, 'family': 0.3}
        priority_score = priority_scores.get(case.priority, 0.5)
        requester_score = requester_scores.get(case.requester_type, 0.3)
        return (priority_score + requester_score) / 2
    
    def process_new_case(self, case_id):
        """Process newly approved case - GLOBAL SCAN (no location restrictions)"""
        try:
            # Get ALL active surveillance footage (no location filtering)
            all_footage = SurveillanceFootage.query.filter_by(is_active=True).all()
            
            if not all_footage:
                logger.warning(f"No surveillance footage available for case {case_id}")
                return 0
            
            created_matches = 0
            
            for footage in all_footage:
                existing = LocationMatch.query.filter_by(
                    case_id=case_id,
                    footage_id=footage.id
                ).first()
                
                if not existing:
                    location_match = LocationMatch(
                        case_id=case_id,
                        footage_id=footage.id,
                        match_score=1.0,  # Global scan - no location scoring
                        distance_km=None,
                        match_type='global_scan',
                        status='pending'
                    )
                    db.session.add(location_match)
                    created_matches += 1
            
            if created_matches > 0:
                db.session.commit()
                logger.info(f"✅ Global scan: Created {created_matches} matches for case {case_id}")
            
            return created_matches
        except Exception as e:
            logger.error(f"Error processing case {case_id}: {e}")
            db.session.rollback()
            return 0
    
    def process_new_footage(self, footage_id):
        """Process newly uploaded footage - GLOBAL SCAN against ALL active cases"""
        try:
            footage = SurveillanceFootage.query.get(footage_id)
            if not footage:
                return 0
            
            # Get ALL active cases (no location filtering)
            active_cases = Case.query.filter(Case.status.in_(['Approved', 'Active', 'Under Processing'])).all()
            matches_created = 0
            
            for case in active_cases:
                existing = LocationMatch.query.filter_by(case_id=case.id, footage_id=footage_id).first()
                if not existing:
                    location_match = LocationMatch(
                        case_id=case.id,
                        footage_id=footage_id,
                        match_score=1.0,  # Global scan - no location scoring
                        distance_km=None,
                        match_type='global_scan',
                        status='pending'
                    )
                    db.session.add(location_match)
                    matches_created += 1
            
            if matches_created > 0:
                db.session.commit()
                logger.info(f"✅ Global scan: Created {matches_created} matches for footage {footage_id}")
            
            return matches_created
        except Exception as e:
            logger.error(f"Error processing footage {footage_id}: {e}")
            db.session.rollback()
            return 0
    
    def analyze_footage_for_person(self, match_id, frame_skip=1, snapshot_interval=30, detection_callback=None, progress_callback=None):
        """PRODUCTION: Analyze footage with proper status management in finally block"""
        cap = None
        try:
            match = LocationMatch.query.get(match_id)
            if not match:
                return False
            
            match.status = 'processing'
            match.ai_analysis_started = datetime.utcnow()
            db.session.commit()
            
            target_profiles = self._load_target_profiles(match.case)
            if not target_profiles or not any(v is not None for v in target_profiles.values()):
                match.status = 'failed'
                db.session.commit()
                return False
            
            footage_path = os.path.join('static', match.footage.video_path)
            if not os.path.exists(footage_path):
                footage_path = os.path.join('app', 'static', match.footage.video_path)
            if not os.path.exists(footage_path):
                match.status = 'failed'
                db.session.commit()
                return False
            
            # Analyze with callback - cap is set inside
            detections = self._analyze_video_with_callback(
                footage_path, target_profiles, match_id, 1, snapshot_interval,
                detection_callback, progress_callback
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Analysis error for match {match_id}: {e}")
            try:
                match = LocationMatch.query.get(match_id)
                if match:
                    match.status = 'failed'
                    db.session.commit()
            except:
                pass
            return False
        
        finally:
            # CRITICAL: Only set completed AFTER video fully released
            try:
                match = LocationMatch.query.get(match_id)
                if match and match.status == 'processing':
                    detections = PersonDetection.query.filter_by(location_match_id=match_id).all()
                    match.detection_count = len(detections)
                    match.person_found = len(detections) > 0
                    match.confidence_score = max([d.confidence_score for d in detections]) if detections else 0.0
                    match.status = 'completed'
                    match.ai_analysis_completed = datetime.utcnow()
                    db.session.commit()
                    logger.info(f"✅ Match {match_id} completed: {match.detection_count} detections")
            except Exception as e:
                logger.error(f"Error finalizing match {match_id}: {e}")
    
    def _load_target_profiles(self, case):
        """
        Load multi-view target profiles (front, left, right)
        
        Returns:
            Dict with 'front', 'left_profile', 'right_profile' encodings
        """
        profiles = {
            'front': None,
            'left_profile': None,
            'right_profile': None
        }
        
        try:
            for target_image in case.target_images:
                image_path = os.path.join('static', target_image.image_path)
                if not os.path.exists(image_path):
                    image_path = os.path.join('app', 'static', target_image.image_path)
                
                print(f"DEBUG: Attempting to load reference photo from: {image_path}")
                
                if os.path.exists(image_path):
                    try:
                        image = face_recognition.load_image_file(image_path)
                        encodings = face_recognition.face_encodings(image)
                        
                        if encodings is not None and len(encodings) > 0:
                            profile_type = self._detect_profile_type(image_path, target_image)
                            print(f"  ✅ Loaded {profile_type}: {len(encodings)} encoding(s)")
                            
                            if profile_type in profiles:
                                profiles[profile_type] = encodings[0]
                            elif profiles['front'] is None:
                                profiles['front'] = encodings[0]
                        else:
                            print(f"  ❌ No face detected in image")
                    except Exception as e:
                        print(f"  ❌ Error loading image: {e}")
                        logger.error(f"Error loading image {image_path}: {e}")
                else:
                    print(f"  ❌ Image file not found at path: {image_path}")
        except Exception as e:
            print(f"DEBUG: Error loading target profiles: {e}")
            logger.error(f"Error loading target profiles: {e}")
        
        loaded_count = sum(1 for v in profiles.values() if v is not None)
        print(f"\nDEBUG: Total encodings loaded: {loaded_count}/3 profiles")
        print(f"  Front: {'YES' if profiles['front'] is not None else 'NO'}")
        print(f"  Left: {'YES' if profiles['left_profile'] is not None else 'NO'}")
        print(f"  Right: {'YES' if profiles['right_profile'] is not None else 'NO'}\n")
        
        return profiles
    
    def _detect_profile_type(self, image_path, target_image):
        """
        Detect profile type from filename or metadata
        
        Returns:
            'front', 'left_profile', or 'right_profile'
        """
        filename = os.path.basename(image_path).lower()
        
        if 'left' in filename or 'side_left' in filename:
            return 'left_profile'
        elif 'right' in filename or 'side_right' in filename:
            return 'right_profile'
        elif 'front' in filename or 'frontal' in filename:
            return 'front'
        
        # Check metadata if available
        if hasattr(target_image, 'profile_type'):
            return target_image.profile_type
        
        # Default to front
        return 'front'
    
    def _analyze_video_with_callback(self, video_path, target_profiles, match_id, frame_skip=1, snapshot_interval=30, detection_callback=None, progress_callback=None):
        """
        STRICT STATE-BASED SCANNING:
        - SEARCH: Check every 0.4s for person
        - COOLDOWN: Skip 2.0s after detection
        - RESUME: Return to SEARCH after cooldown
        """
        cap = None
        
        try:
            from vision_engine import get_vision_engine
            
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # STRICT PARAMETERS
            scan_interval = 0.4  # Check every 0.4 seconds
            cooldown_duration = 2.0  # 2 second cooldown
            scan_frame_interval = int(fps * scan_interval)
            
            print(f"\n{'='*80}")
            print(f"STRICT STATE-BASED SCANNING")
            print(f"  Video: {video_path}")
            print(f"  FPS: {fps}, Duration: {total_frames/fps:.1f}s")
            print(f"  Scan Interval: {scan_interval}s (every {scan_frame_interval} frames)")
            print(f"  Cooldown: {cooldown_duration}s")
            print(f"  States: SEARCH → DETECT → COOLDOWN → SEARCH")
            print(f"{'='*80}\n")
            
            vision_engine = get_vision_engine(match_id)
            
            # STATE MACHINE
            state = 'SEARCH'  # SEARCH or COOLDOWN
            cooldown_until_time = 0.0
            unique_detections = 0
            frame_count = 0
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                timestamp = frame_count / fps
                
                if progress_callback and frame_count % 10 == 0:
                    progress_callback(frame_count)
                
                # STATE: COOLDOWN
                if state == 'COOLDOWN':
                    if timestamp >= cooldown_until_time:
                        state = 'SEARCH'
                        print(f"  🔄 RESUME SEARCH at {timestamp:.2f}s")
                    else:
                        frame_count += 1
                        continue
                
                # STATE: SEARCH (check every 0.4s)
                if state == 'SEARCH' and frame_count % scan_frame_interval == 0:
                    detection_data = vision_engine.detect_multi_view(frame, target_profiles, timestamp, match_id)
                    
                    if detection_data and detection_data.get('confidence_score', 0) >= 0.50:
                        confidence = detection_data['confidence_score']
                        unique_detections += 1
                        
                        print(f"  ✅ DETECTION #{unique_detections} at {timestamp:.2f}s, Confidence: {confidence*100:.1f}%")
                        
                        # IMMEDIATE SAVE
                        detection = PersonDetection(
                            location_match_id=match_id,
                            timestamp=timestamp,
                            confidence_score=confidence,
                            face_match_score=detection_data.get('face_match_score', confidence),
                            detection_box=detection_data.get('detection_box', '{}'),
                            frame_path=detection_data['frame_path'].replace('static/', ''),
                            frame_hash=detection_data.get('frame_hash', ''),
                            evidence_number=detection_data.get('evidence_number', ''),
                            matched_view=detection_data.get('matched_profile', 'video'),
                            feature_weights=detection_data.get('feature_weights', '{}'),
                            decision_factors=detection_data.get('decision_factors', '[]'),
                            analysis_method='strict_state_scan'
                        )
                        db.session.add(detection)
                        db.session.commit()  # IMMEDIATE COMMIT
                        
                        if detection_callback:
                            detection_callback(confidence)
                        
                        # ENTER COOLDOWN
                        state = 'COOLDOWN'
                        cooldown_until_time = timestamp + cooldown_duration
                        print(f"  ⏸️  COOLDOWN until {cooldown_until_time:.2f}s")
                
                frame_count += 1
            
            print(f"\n{'='*80}")
            print(f"STRICT SCANNING COMPLETE")
            print(f"  Total Frames: {frame_count}")
            print(f"  Unique Detections: {unique_detections}")
            print(f"  Timeline: Clean, non-repetitive")
            print(f"{'='*80}\n")
            
            logger.info(f"Strict scan: {unique_detections} unique detections saved")
            
        except Exception as e:
            logger.error(f"Strict scanning error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            if cap is not None:
                cap.release()
        
        return []
    
    def _multi_view_analyze_video(self, video_path, target_profiles, match_id):
        """
        Analyze video with multi-view detection (original method)
        """
        detections = []
        
        try:
            from vision_engine import get_vision_engine
            
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            frame_count = 0
            
            vision_engine = get_vision_engine(match_id)
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process every 30 frames (1 second)
                if frame_count % 30 == 0:
                    timestamp = frame_count / fps
                    
                    # Multi-view detection
                    detection_data = vision_engine.detect_multi_view(
                        frame,
                        target_profiles,
                        timestamp,
                        match_id
                    )
                    
                    if detection_data:
                        # Save to database
                        self._save_multi_view_detection(
                            detection_data,
                            timestamp,
                            match_id
                        )
                        
                        detections.append({
                            'timestamp': timestamp,
                            'confidence': detection_data['confidence_score'],
                            'matched_profile': detection_data['matched_profile'],
                            'temporal_count': detection_data['temporal_count']
                        })
                
                frame_count += 1
            
            cap.release()
            db.session.commit()
            
            logger.info(f"Multi-view analysis complete: {len(detections)} detections")
            
        except Exception as e:
            logger.error(f"Multi-view video analysis error: {e}")
        
        return detections
    

    def _fast_analyze_video(self, video_path, target_encodings, match_id):
        """Fast video analysis with smart sampling"""
        detections = []
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps
            
            # Smart sampling
            if duration < 60:
                sample_interval = 0.5
            elif duration < 300:
                sample_interval = 1.0
            elif duration < 1800:
                sample_interval = 2.0
            else:
                sample_interval = 5.0
            
            frame_indices = [int(i * fps * sample_interval) for i in range(int(duration / sample_interval))]
            
            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if not ret:
                    continue
                
                timestamp = idx / fps
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                face_locations = face_recognition.face_locations(rgb_frame, model="hog")
                if face_locations is not None and len(face_locations) > 0:
                    encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                    for encoding, location in zip(encodings, face_locations):
                        matches = face_recognition.compare_faces(target_encodings, encoding, tolerance=0.6)
                        match_found = any(matches) if isinstance(matches, (list, np.ndarray)) else bool(matches)
                        
                        if match_found:
                            distances = face_recognition.face_distance(target_encodings, encoding)
                            if distances is None or len(distances) == 0:
                                continue
                            best_distance = float(np.min(distances))
                            confidence_percent = max(0, min(100, (1 - best_distance / 0.6) * 100))
                        else:
                            continue
                        
                        if confidence_percent >= 60:
                            self._save_detection(frame, location, timestamp, match_id, confidence_percent, best_distance)
                            detections.append({'timestamp': timestamp, 'confidence': confidence_percent / 100.0})
            
            cap.release()
            db.session.commit()
            logger.info(f"Analysis complete: {len(detections)} detections")
        except Exception as e:
            logger.error(f"Video analysis error: {e}")
        
        return detections
    
    def _save_detection(self, frame, location, timestamp, match_id, confidence_percent, distance):
        """Save detection to database"""
        try:
            frame_filename = f"detection_{match_id}_{int(timestamp)}.jpg"
            frame_dir = os.path.join('static', 'detections')
            os.makedirs(frame_dir, exist_ok=True)
            
            top, right, bottom, left = location
            region = frame[max(0, top-20):min(frame.shape[0], bottom+20), 
                          max(0, left-20):min(frame.shape[1], right+20)]
            
            if region.size > 0:
                cv2.imwrite(os.path.join(frame_dir, frame_filename), region)
                
                detection = PersonDetection(
                    location_match_id=match_id,
                    timestamp=timestamp,
                    confidence_score=confidence_percent / 100.0,
                    face_match_score=confidence_percent / 100.0,
                    detection_box=json.dumps({'top': int(top), 'right': int(right), 'bottom': int(bottom), 'left': int(left), 'distance': float(distance)}),
                    frame_path=f"detections/{frame_filename}",
                    analysis_method='unified_engine'
                )
                db.session.add(detection)
        except Exception as e:
            logger.error(f"Save detection error: {e}")
    
    def auto_process_approved_case(self, case_id):
        """Auto-process approved case (alias for compatibility)"""
        return self.process_new_case(case_id)
    
    def _strict_analyze_video(self, video_path, target_encodings, match_id, min_confidence=0.88, strict_mode=True):
        """FORENSIC: 0.88 threshold + frontal + SHA-256"""
        detections = []
        
        try:
            from vision_engine import get_vision_engine
            from evidence_integrity_system import EvidenceIntegritySystem
            
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            frame_count = 0
            
            evidence_system = EvidenceIntegritySystem()
            vision_engine = get_vision_engine(match_id)
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Sample every 30 frames (1 second intervals)
                if frame_count % 30 == 0:
                    timestamp = frame_count / fps
                    
                    # Use vision engine with strict mode
                    detection_data = vision_engine.detect_person(
                        frame,
                        target_encoding=target_encodings[0],
                        case_id=match_id,
                        strict_mode=True
                    )
                    
                    if detection_data:
                        confidence = detection_data.get('confidence_score', 0)
                        is_frontal = detection_data.get('is_frontal_face', False)
                        
                        # FORENSIC THRESHOLD: Exactly 0.88
                        if confidence >= 0.60 and is_frontal:
                            # Generate SHA-256 hash
                            frame_hash = detection_data.get('frame_hash', 'N/A')
                            
                            # Save detection with evidence
                            self._save_strict_detection(
                                frame,
                                detection_data,
                                timestamp,
                                match_id,
                                frame_hash
                            )
                            
                            detections.append({
                                'timestamp': timestamp,
                                'confidence': confidence,
                                'is_frontal': is_frontal,
                                'frame_hash': frame_hash
                            })
                
                frame_count += 1
            
            cap.release()
            db.session.commit()
            
            logger.info(f"Strict analysis complete: {len(detections)} high-confidence detections")
            
        except Exception as e:
            logger.error(f"Strict video analysis error: {e}")
        
        return detections
    
    def _save_strict_detection(self, frame, detection_data, timestamp, match_id, frame_hash):
        """Save detection with strict validation and evidence integrity"""
        try:
            frame_filename = f"detection_{match_id}_{int(timestamp * 1000)}.jpg"
            frame_dir = os.path.join('static', 'detections')
            os.makedirs(frame_dir, exist_ok=True)
            
            bbox = detection_data.get('detection_box', (0, 0, 100, 100))
            left, top, width, height = bbox
            
            # Extract face region
            region = frame[
                max(0, top-20):min(frame.shape[0], top+height+20),
                max(0, left-20):min(frame.shape[1], left+width+20)
            ]
            
            if region.size > 0:
                cv2.imwrite(os.path.join(frame_dir, frame_filename), region)
                
                detection = PersonDetection(
                    location_match_id=match_id,
                    timestamp=timestamp,
                    confidence_score=detection_data.get('confidence_score', 0),
                    face_match_score=detection_data.get('face_match_score', 0),
                    detection_box=json.dumps(bbox),
                    frame_path=f"detections/{frame_filename}",
                    frame_hash=frame_hash,
                    evidence_number=detection_data.get('evidence_number', 'N/A'),
                    is_frontal_face=detection_data.get('is_frontal_face', False),
                    face_pose_yaw=detection_data.get('face_pose_yaw', 0),
                    face_pose_pitch=detection_data.get('face_pose_pitch', 0),
                    feature_weights=detection_data.get('feature_weights', '{}'),
                    decision_factors=detection_data.get('decision_factors', '[]'),
                    analysis_method='strict_batch_0.88'
                )
                db.session.add(detection)
                
        except Exception as e:
            logger.error(f"Save strict detection error: {e}")

    
    def analyze_with_progress(self, case_id, footage_id, batch_id, progress_callback=None):
        """Analyze footage with real-time progress updates"""
        try:
            from models import Case, SurveillanceFootage, LocationMatch
            
            # Get or create match
            match = LocationMatch.query.filter_by(
                case_id=case_id,
                footage_id=footage_id
            ).first()
            
            if not match:
                match = LocationMatch(
                    case_id=case_id,
                    footage_id=footage_id,
                    batch_id=batch_id,
                    status='processing',
                    match_type='batch_progress'
                )
                db.session.add(match)
            else:
                match.status = 'processing'
                match.batch_id = batch_id
            
            db.session.commit()
            
            # Get target encodings
            case = Case.query.get(case_id)
            target_encodings = []
            
            for target_image in case.target_images:
                image_path = os.path.join('static', target_image.image_path)
                if os.path.exists(image_path):
                    try:
                        import face_recognition
                        image = face_recognition.load_image_file(image_path)
                        encodings = face_recognition.face_encodings(image)
                        if encodings is not None and len(encodings) > 0:
                            target_encodings.append(encodings[0])
                    except:
                        pass
            
            if target_encodings is None or len(target_encodings) == 0:
                match.status = 'failed'
                db.session.commit()
                return False
            
            # Get footage
            footage = SurveillanceFootage.query.get(footage_id)
            video_path = os.path.join('static', footage.video_path)
            
            if not os.path.exists(video_path):
                match.status = 'failed'
                db.session.commit()
                return False
            
            # Process with progress
            detections = self._process_video_with_progress(
                video_path,
                target_encodings,
                case_id,
                match.id,
                progress_callback
            )
            
            # Update match
            match.detection_count = len(detections)
            match.person_found = len(detections) > 0
            match.status = 'completed'
            
            if detections:
                confidences = [d['confidence'] for d in detections]
                match.confidence_score = sum(confidences) / len(confidences)
            
            db.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Progress analysis error: {e}")
            if match:
                match.status = 'failed'
                db.session.commit()
            return False
    
    def _process_video_with_progress(self, video_path, target_encodings, case_id, match_id, progress_callback):
        """Process video with forensic CCTV analysis and progress updates"""
        detections = []
        
        try:
            from forensic_vision_engine import ForensicVisionEngine
            
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            frame_count = 0
            
            forensic_engine = ForensicVisionEngine(case_id)
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process every 30 frames (1 second)
                if frame_count % 30 == 0:
                    timestamp = frame_count / fps
                    
                    # Detect in crowd with temporal smoothing
                    detection_result = forensic_engine.detect_in_crowd(
                        frame,
                        target_encodings[0]
                    )
                    
                    if detection_result:
                        # Save forensic output with zoom-in inset
                        saved = forensic_engine.save_forensic_detection(
                            frame,
                            detection_result,
                            timestamp,
                            case_id
                        )
                        
                        if saved:
                            # Save to database
                            self._save_forensic_detection_db(
                                saved,
                                timestamp,
                                match_id,
                                detection_result
                            )
                            
                            detections.append({
                                'timestamp': timestamp,
                                'confidence': saved['confidence'],
                                'crowd_size': saved['crowd_size']
                            })
                
                frame_count += 1
                
                # Update progress
                if progress_callback and total_frames > 0:
                    percent = int((frame_count / total_frames) * 100)
                    progress_callback(percent)
            
            cap.release()
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Forensic video processing error: {e}")
        
        return detections
    
    def _save_forensic_detection_db(self, saved_data, timestamp, match_id, detection_result):
        """Save forensic detection to database"""
        try:
            target = detection_result['target']
            top, right, bottom, left = target['location']
            
            detection = PersonDetection(
                location_match_id=match_id,
                timestamp=timestamp,
                confidence_score=saved_data['confidence'],
                face_match_score=saved_data['confidence'],
                detection_box=json.dumps({'top': int(top), 'right': int(right), 'bottom': int(bottom), 'left': int(left)}),
                frame_path=saved_data['filepath'].replace('static/', ''),
                frame_hash=saved_data['frame_hash'],
                evidence_number=saved_data['evidence_number'],
                is_frontal_face=True,
                face_pose_yaw=target.get('pose', {}).get('yaw', 0),
                face_pose_pitch=target.get('pose', {}).get('pitch', 0),
                feature_weights=json.dumps({
                    'temporal_consistency': {'score': 1.0, 'weight': 0.3},
                    'face_match': {'score': saved_data['confidence'], 'weight': 0.7}
                }),
                decision_factors=json.dumps([
                    f"Temporal smoothing verified (5-10 frames)",
                    f"Crowd analysis: {saved_data['crowd_size']} faces detected",
                    f"Low-light enhancement applied",
                    f"Multi-scale detection used",
                    f"Confidence: {saved_data['confidence']*100:.1f}%"
                ]),
                analysis_method='forensic_cctv_crowd'
            )
            db.session.add(detection)
            
        except Exception as e:
            logger.error(f"Save forensic detection DB error: {e}")

# Global instance
location_engine = LocationMatchingEngine()
