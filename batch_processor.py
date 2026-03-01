"""
Batch Processor with 0.88 Threshold and Strict Frontal-Face Detection
"""
import cv2
import face_recognition
import numpy as np
import json
import os
from models import db, Case, SurveillanceFootage, LocationMatch, PersonDetection
from evidence_integrity_system import EvidenceIntegritySystem
import logging

logger = logging.getLogger(__name__)

STRICT_THRESHOLD = 0.88


def is_frontal_face_strict(face_landmarks):
    """Verify both eyes and nose are visible"""
    if not face_landmarks:
        return False
    return all(k in face_landmarks for k in ['left_eye', 'right_eye', 'nose_tip'])


def is_person_class(frame, bbox):
    """Filter out posters, statues, non-human objects"""
    try:
        x, y, w, h = bbox
        roi = frame[y:y+h, x:x+w]
        
        # Real person has texture variance
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        texture_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Real person has color depth
        color_std = np.std(roi)
        
        return texture_var > 10 and color_std > 15
        
    except:
        return True


def analyze_single_footage_strict(case_id, footage_id, batch_id):
    """Analyze single footage with strict rules"""
    case = Case.query.get(case_id)
    footage = SurveillanceFootage.query.get(footage_id)
    
    if not case or not footage:
        return {'error': 'Not found'}
    
    # Get target encodings
    target_encodings = []
    for img in case.target_images:
        try:
            img_path = os.path.join('static', img.image_path)
            image = face_recognition.load_image_file(img_path)
            encodings = face_recognition.face_encodings(image)
            target_encodings.extend(encodings)
        except Exception as e:
            logger.error(f"Target load error: {e}")
    
    if not target_encodings:
        return {'error': 'No target encodings'}
    
    # Create match record
    match = LocationMatch(
        case_id=case_id,
        footage_id=footage_id,
        status='processing',
        batch_id=batch_id
    )
    db.session.add(match)
    db.session.flush()
    
    # Analyze video
    video_path = os.path.join('static', footage.video_path)
    detections = []
    
    if os.path.exists(video_path):
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        frame_count = 0
        evidence_system = EvidenceIntegritySystem()
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process every 30 frames (1 per second)
            if frame_count % 30 == 0:
                timestamp = frame_count / fps
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Detect faces
                face_locations = face_recognition.face_locations(rgb_frame, model='hog')
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                face_landmarks_list = face_recognition.face_landmarks(rgb_frame, face_locations)
                
                for idx, (face_loc, face_enc) in enumerate(zip(face_locations, face_encodings)):
                    # Check frontal face
                    if idx < len(face_landmarks_list):
                        if not is_frontal_face_strict(face_landmarks_list[idx]):
                            continue
                    
                    # Match against targets
                    for target_enc in target_encodings:
                        distance = face_recognition.face_distance([target_enc], face_enc)[0]
                        confidence = max(0.0, 1.0 - distance)
                        
                        # Apply strict 0.88 threshold
                        if confidence < STRICT_THRESHOLD:
                            continue
                        
                        # Convert location to bbox
                        top, right, bottom, left = face_loc
                        bbox = (left, top, right - left, bottom - top)
                        
                        # Verify person class
                        if not is_person_class(frame, bbox):
                            continue
                        
                        # Generate evidence with SHA-256 hash
                        evidence = evidence_system.create_evidence_frame(
                            {
                                'case_id': case_id,
                                'footage_id': footage_id,
                                'timestamp': timestamp,
                                'bbox': bbox,
                                'confidence': confidence,
                                'method': 'strict_batch'
                            },
                            frame
                        )
                        
                        # Save detection
                        detection = PersonDetection(
                            location_match_id=match.id,
                            timestamp=timestamp,
                            confidence_score=confidence,
                            frame_hash=evidence.frame_hash,
                            evidence_number=evidence.evidence_number,
                            detection_box=json.dumps(bbox),
                            is_frontal_face=True,
                            batch_id=batch_id,
                            analysis_method='strict_frontal_0.88'
                        )
                        db.session.add(detection)
                        detections.append(detection)
                        break
            
            frame_count += 1
        
        cap.release()
    
    # Update match
    match.status = 'completed'
    match.detection_count = len(detections)
    match.person_found = len(detections) > 0
    
    db.session.commit()
    
    return {
        'footage_id': footage_id,
        'detections': len(detections),
        'high_confidence': len([d for d in detections if d.confidence_score > 0.9])
    }


def process_batch_direct(case_id, footage_ids, batch_id):
    """Direct processing without Celery"""
    results = []
    for fid in footage_ids:
        result = analyze_single_footage_strict(case_id, fid, batch_id)
        results.append(result)
    
    return {
        'total_detections': sum(r.get('detections', 0) for r in results),
        'results': results
    }
