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
        
        self.CASE_CRITERIA = {
            'missing_person': {'radius_km': 25, 'time_window_hours': 168, 'confidence_threshold': 0.4},
            'criminal_investigation': {'radius_km': 10, 'time_window_hours': 72, 'confidence_threshold': 0.6},
            'surveillance_request': {'radius_km': 5, 'time_window_hours': 24, 'confidence_threshold': 0.7},
            'person_tracking': {'radius_km': 50, 'time_window_hours': 336, 'confidence_threshold': 0.3},
            'evidence_analysis': {'radius_km': 15, 'time_window_hours': 120, 'confidence_threshold': 0.5}
        }
        
        self.PRIORITY_RADIUS = {'Critical': 2.0, 'High': 1.5, 'Medium': 1.0, 'Low': 0.7}
        self.REQUESTER_BOOST = {'police': 2.0, 'government': 1.8, 'private_investigator': 1.5, 'organization': 1.3, 'family': 1.0}
    
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
        """Find matches using GPS + string matching"""
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
            match_score = 0.0
            distance_km = None
            
            # GPS matching (40% weight)
            if footage.latitude and footage.longitude:
                distance_km = geodesic((case_lat, case_lon), (footage.latitude, footage.longitude)).kilometers
                if distance_km <= search_radius:
                    geo_score = max(0, 1 - (distance_km / search_radius))
                    match_score += geo_score * 0.4
                else:
                    continue
            
            # String matching (60% weight)
            name_score = self._calculate_name_similarity(case.last_seen_location, footage.location_name)
            match_score += name_score * 0.6
            
            if match_score > 0.3:
                matches.append({
                    'footage': footage,
                    'match_score': min(match_score, 1.0),
                    'distance_km': distance_km,
                    'match_type': 'intelligent'
                })
        
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
    
    def _calculate_name_similarity(self, case_location, footage_location):
        """Calculate location name similarity"""
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
    
    def process_new_case(self, case_id):
        """Process newly approved case"""
        try:
            matches = self.find_location_matches(case_id)
            created_matches = 0
            
            for match_data in matches:
                existing = LocationMatch.query.filter_by(
                    case_id=case_id,
                    footage_id=match_data['footage'].id
                ).first()
                
                if not existing:
                    location_match = LocationMatch(
                        case_id=case_id,
                        footage_id=match_data['footage'].id,
                        match_score=match_data['match_score'],
                        distance_km=match_data['distance_km'],
                        match_type=match_data.get('match_type', 'auto'),
                        status='pending'
                    )
                    db.session.add(location_match)
                    created_matches += 1
            
            if created_matches > 0:
                db.session.commit()
                logger.info(f"Created {created_matches} location matches for case {case_id}")
            
            return created_matches
        except Exception as e:
            logger.error(f"Error processing case {case_id}: {e}")
            db.session.rollback()
            return 0
    
    def process_new_footage(self, footage_id):
        """Process newly uploaded footage"""
        try:
            footage = SurveillanceFootage.query.get(footage_id)
            if not footage:
                return 0
            
            active_cases = Case.query.filter(Case.status.in_(['Approved', 'Active', 'Under Processing'])).all()
            matches_created = 0
            
            for case in active_cases:
                match_score = self._calculate_name_similarity(case.last_seen_location, footage.location_name)
                
                if match_score > 0.2:
                    existing = LocationMatch.query.filter_by(case_id=case.id, footage_id=footage_id).first()
                    if not existing:
                        location_match = LocationMatch(
                            case_id=case.id,
                            footage_id=footage_id,
                            match_score=match_score,
                            distance_km=None,
                            status='pending'
                        )
                        db.session.add(location_match)
                        matches_created += 1
            
            if matches_created > 0:
                db.session.commit()
                logger.info(f"Created {matches_created} matches for footage {footage_id}")
            
            return matches_created
        except Exception as e:
            logger.error(f"Error processing footage {footage_id}: {e}")
            db.session.rollback()
            return 0
    
    def analyze_footage_for_person(self, match_id):
        """Analyze footage using AI detection"""
        try:
            match = LocationMatch.query.get(match_id)
            if not match:
                return False
            
            match.status = 'processing'
            match.ai_analysis_started = datetime.utcnow()
            db.session.commit()
            
            # Get target encodings
            target_encodings = []
            for target_image in match.case.target_images:
                image_path = os.path.join('static', target_image.image_path)
                if not os.path.exists(image_path):
                    image_path = os.path.join('app', 'static', target_image.image_path)
                
                if os.path.exists(image_path):
                    try:
                        image = face_recognition.load_image_file(image_path)
                        encodings = face_recognition.face_encodings(image)
                        if encodings:
                            target_encodings.append(encodings[0])
                    except:
                        pass
            
            if not target_encodings:
                match.status = 'failed'
                db.session.commit()
                return False
            
            # Get footage path
            footage_path = os.path.join('static', match.footage.video_path)
            if not os.path.exists(footage_path):
                footage_path = os.path.join('app', 'static', match.footage.video_path)
            if not os.path.exists(footage_path):
                match.status = 'failed'
                db.session.commit()
                return False
            
            # Analyze video
            detections = self._fast_analyze_video(footage_path, target_encodings, match_id)
            
            match.detection_count = len(detections)
            match.person_found = len(detections) > 0
            
            if detections:
                confidences = [d['confidence'] for d in detections]
                match.confidence_score = sum(confidences) / len(confidences)
                match.match_score = match.confidence_score
            else:
                match.confidence_score = 0.0
            
            match.status = 'completed'
            match.ai_analysis_completed = datetime.utcnow()
            db.session.commit()
            
            return True
        except Exception as e:
            logger.error(f"Analysis error for match {match_id}: {e}")
            if match:
                match.status = 'failed'
                db.session.commit()
            return False
    
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
                if face_locations:
                    encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                    for encoding, location in zip(encodings, face_locations):
                        distances = face_recognition.face_distance(target_encodings, encoding)
                        best_distance = float(np.min(distances))
                        confidence_percent = max(0, min(100, (1 - best_distance / 0.6) * 100))
                        
                        if confidence_percent >= 40:
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

# Global instance
location_engine = LocationMatchingEngine()
