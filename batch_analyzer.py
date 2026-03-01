"""
Batch Analyzer with Strict Frontal-Face Detection
"""
import cv2
import face_recognition
import numpy as np
from vision_engine import get_vision_engine
from models import db, PersonDetection, LocationMatch
import logging

logger = logging.getLogger(__name__)

class StrictFrontalFaceDetector:
    """Enforces strict frontal-face detection rules"""
    
    MATCH_THRESHOLD = 0.85
    
    @staticmethod
    def is_frontal_face(face_landmarks):
        """Check if face is frontal (both eyes and nose visible)"""
        if not face_landmarks:
            return False
        
        required_features = ['left_eye', 'right_eye', 'nose_tip']
        return all(feature in face_landmarks for feature in required_features)
    
    @staticmethod
    def is_person_not_object(frame, bbox):
        """Verify detection is a person, not statue/poster"""
        try:
            x, y, w, h = bbox
            roi = frame[y:y+h, x:x+w]
            
            # Check for motion blur (real people move)
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Check color variance (posters are flat)
            color_std = np.std(roi)
            
            # Real person: some blur + color variance
            return laplacian_var > 10 and color_std > 15
            
        except Exception as e:
            logger.warning(f"Object check failed: {e}")
            return True  # Assume person if check fails
    
    @staticmethod
    def validate_detection(frame, face_location, face_encoding, target_encoding):
        """Strict validation: frontal face + person check + threshold"""
        try:
            # Get face landmarks
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            landmarks = face_recognition.face_landmarks(rgb_frame, [face_location])
            
            if not landmarks:
                return None
            
            # Check frontal face
            if not StrictFrontalFaceDetector.is_frontal_face(landmarks[0]):
                return None
            
            # Calculate match score
            distance = face_recognition.face_distance([target_encoding], face_encoding)[0]
            match_score = max(0.0, 1.0 - distance)
            
            # Apply strict threshold
            if match_score < StrictFrontalFaceDetector.MATCH_THRESHOLD:
                return None
            
            # Convert face_location to bbox
            top, right, bottom, left = face_location
            bbox = (left, top, right - left, bottom - top)
            
            # Check if person (not object)
            if not StrictFrontalFaceDetector.is_person_not_object(frame, bbox):
                return None
            
            return {
                'match_score': match_score,
                'bbox': bbox,
                'is_frontal': True,
                'landmarks': landmarks[0]
            }
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return None


def process_batch_sync(case_id, footage_ids, batch_id):
    """Synchronous batch processing"""
    from models import Case, SurveillanceFootage
    from evidence_integrity_system import EvidenceIntegritySystem
    
    case = Case.query.get(case_id)
    if not case:
        return {'error': 'Case not found'}
    
    # Get target encodings
    target_encodings = []
    for img in case.target_images:
        try:
            image_path = os.path.join('static', img.image_path)
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            target_encodings.extend(encodings)
        except Exception as e:
            logger.error(f"Error loading target image: {e}")
    
    if not target_encodings:
        return {'error': 'No valid target encodings'}
    
    evidence_system = EvidenceIntegritySystem()
    detector = StrictFrontalFaceDetector()
    results = []
    
    for footage_id in footage_ids:
        footage = SurveillanceFootage.query.get(footage_id)
        if not footage:
            continue
        
        # Create location match
        match = LocationMatch(
            case_id=case_id,
            footage_id=footage_id,
            status='processing',
            batch_id=batch_id
        )
        db.session.add(match)
        db.session.flush()
        
        # Analyze footage
        detections = analyze_footage_strict(
            footage, 
            target_encodings, 
            match.id, 
            batch_id,
            evidence_system,
            detector
        )
        
        match.status = 'completed'
        match.detection_count = len(detections)
        match.person_found = len(detections) > 0
        
        results.append({
            'footage_id': footage_id,
            'detections': len(detections)
        })
    
    db.session.commit()
    return {'results': results, 'total_detections': sum(r['detections'] for r in results)}


def analyze_footage_strict(footage, target_encodings, match_id, batch_id, evidence_system, detector):
    """Analyze single footage with strict rules"""
    import os
    
    video_path = os.path.join('static', footage.video_path)
    if not os.path.exists(video_path):
        return []
    
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_count = 0
    detections = []
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Process every 30th frame (1 per second at 30fps)
        if frame_count % 30 == 0:
            timestamp = frame_count / fps
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            face_locations = face_recognition.face_locations(rgb_frame, model='hog')
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            for face_location, face_encoding in zip(face_locations, face_encodings):
                # Try each target encoding
                for target_encoding in target_encodings:
                    result = detector.validate_detection(
                        frame, 
                        face_location, 
                        face_encoding, 
                        target_encoding
                    )
                    
                    if result:
                        # Generate evidence
                        evidence = evidence_system.create_evidence_frame(
                            {
                                'case_id': match_id,
                                'footage_id': footage.id,
                                'timestamp': timestamp,
                                'bbox': result['bbox'],
                                'confidence': result['match_score'],
                                'method': 'strict_frontal'
                            },
                            frame
                        )
                        
                        # Save detection
                        detection = PersonDetection(
                            location_match_id=match_id,
                            timestamp=timestamp,
                            confidence_score=result['match_score'],
                            frame_hash=evidence.frame_hash,
                            evidence_number=evidence.evidence_number,
                            detection_box=json.dumps(result['bbox']),
                            is_frontal_face=True,
                            batch_id=batch_id,
                            analysis_method='strict_frontal_batch'
                        )
                        db.session.add(detection)
                        detections.append(detection)
                        break  # Only one match per face
        
        frame_count += 1
    
    cap.release()
    db.session.commit()
    return detections
