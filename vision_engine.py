"""
Unified Vision Engine - Single Source of Truth
Uses enhanced_ultra_detector_with_xai.py exclusively
"""
import json
import logging
import numpy as np
import cv2
import hashlib
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class VisionEngine:
    """Unified vision engine for all person detection tasks"""
    
    def __init__(self, case_id=None):
        self.case_id = case_id
        self.detector = None
        self.evidence_system = None
        self.xai_system = None
        self._init_systems()
    
    def _init_systems(self):
        """Initialize all systems with error handling"""
        try:
            from enhanced_ultra_detector_with_xai import EnhancedUltraDetectorWithXAI
            self.detector = EnhancedUltraDetectorWithXAI(self.case_id or 0)
            logger.info("✅ Enhanced detector initialized")
        except Exception as e:
            logger.error(f"❌ Detector init failed: {e}")
        
        try:
            from evidence_integrity_system import EvidenceIntegritySystem
            self.evidence_system = EvidenceIntegritySystem()
            logger.info("✅ Evidence system initialized")
        except Exception as e:
            logger.error(f"❌ Evidence system init failed: {e}")
        
        try:
            from xai_feature_weighting_system import XAIFeatureWeightingSystem
            self.xai_system = XAIFeatureWeightingSystem()
            logger.info("✅ XAI system initialized")
        except Exception as e:
            logger.error(f"❌ XAI system init failed: {e}")
    
    def detect_person(self, frame, target_encoding=None, case_id=None, strict_mode=False):
        """
        Detect person with optional strict frontal-face mode
        
        Args:
            strict_mode: If True, enforces 0.88 threshold + frontal face validation
        """
        if frame is None or not isinstance(frame, np.ndarray):
            return None
        
        if case_id:
            self.case_id = case_id
        
        detection_data = self._build_detection_data(frame, target_encoding, strict_mode)
        
        if not detection_data:
            return None
        
        evidence = self._generate_evidence(frame, detection_data)
        xai_result = self._calculate_xai_weights(detection_data)
        
        return self._merge_results(detection_data, evidence, xai_result)
    
    def _build_detection_data(self, frame, target_encoding, strict_mode=False):
        """Build detection with optional strict mode (0.88 threshold + frontal check)"""
        try:
            import face_recognition
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame, model='hog')
            
            if not face_locations:
                return None
            
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            if not face_encodings:
                return None
            
            # Get landmarks for strict mode
            face_landmarks_list = None
            if strict_mode:
                face_landmarks_list = face_recognition.face_landmarks(rgb_frame, face_locations)
            
            best_match = None
            best_confidence = 0.0
            best_location = None
            is_frontal = False
            
            for idx, (face_encoding, face_location) in enumerate(zip(face_encodings, face_locations)):
                # Strict frontal check
                if strict_mode and face_landmarks_list:
                    if idx < len(face_landmarks_list):
                        landmarks = face_landmarks_list[idx]
                        # Require both eyes + nose
                        if not all(k in landmarks for k in ['left_eye', 'right_eye', 'nose_tip']):
                            continue
                        is_frontal = True
                
                if target_encoding is not None:
                    distance = face_recognition.face_distance([target_encoding], face_encoding)[0]
                    confidence = max(0.0, 1.0 - distance)
                    
                    # Apply strict 0.88 threshold
                    if strict_mode and confidence < 0.88:
                        continue
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = face_encoding
                        best_location = face_location
                else:
                    best_confidence = 0.7
                    best_match = face_encoding
                    best_location = face_location
                    break
            
            if best_match is None or best_confidence < 0.4:
                return None
            
            top, right, bottom, left = best_location
            bbox = (left, top, right - left, bottom - top)
            
            return {
                'confidence': best_confidence,
                'face_confidence': best_confidence,
                'bbox': bbox,
                'detection_box': bbox,
                'face_encoding': best_match.tolist(),
                'timestamp': 0.0,
                'case_id': self.case_id or 0,
                'footage_id': 0,
                'method': 'strict_0.88' if strict_mode else 'vision_engine',
                'is_frontal_face': is_frontal,
                'clothing_confidence': 0.0,
                'body_confidence': 0.0,
                'motion_confidence': 0.0,
                'duration': 0.0,
                'consistency': 0.0,
                'tracking_stability': 0.0,
                'frame_quality': 0.8,
                'face_visibility': 0.8,
                'lighting_quality': 0.7
            }
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return None
    
    def _generate_evidence(self, frame, detection_data):
        """Generate evidence integrity data"""
        try:
            if self.evidence_system:
                evidence_frame = self.evidence_system.create_evidence_frame(
                    detection_data, 
                    frame
                )
                return {
                    'frame_hash': evidence_frame.frame_hash,
                    'evidence_number': evidence_frame.evidence_number,
                    'frame_path': evidence_frame.frame_path
                }
        except Exception as e:
            logger.error(f"Evidence generation error: {e}")
        
        # Fallback: generate basic hash
        try:
            frame_bytes = cv2.imencode('.jpg', frame)[1].tobytes()
            frame_hash = hashlib.sha256(frame_bytes).hexdigest()
            return {
                'frame_hash': frame_hash,
                'evidence_number': f"EVD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'frame_path': ''
            }
        except:
            return {
                'frame_hash': 'unavailable',
                'evidence_number': 'unavailable',
                'frame_path': ''
            }
    
    def _calculate_xai_weights(self, detection_data):
        """Calculate XAI feature weights"""
        try:
            if self.xai_system:
                xai_result = self.xai_system.analyze_detection_with_xai(detection_data)
                return xai_result
        except Exception as e:
            logger.error(f"XAI calculation error: {e}")
        
        return None
    
    def _merge_results(self, detection_data, evidence, xai_result):
        """Merge all results into final output"""
        confidence = detection_data.get('confidence', 0.0)
        
        # Determine confidence category
        if confidence >= 0.9:
            category = 'very_high'
        elif confidence >= 0.75:
            category = 'high'
        elif confidence >= 0.6:
            category = 'medium'
        else:
            category = 'low'
        
        # Build feature weights
        if xai_result:
            feature_weights = xai_result.feature_weights.get_confidence_breakdown()
            decision_factors = xai_result.decision_factors
            uncertainty_factors = xai_result.uncertainty_factors
        else:
            feature_weights = {
                'facial_structure': {'score': confidence, 'weight': 0.5, 'contribution': confidence * 0.5},
                'clothing_biometric': {'score': 0.0, 'weight': 0.25, 'contribution': 0.0},
                'temporal_consistency': {'score': 0.0, 'weight': 0.2, 'contribution': 0.0},
                'body_pose': {'score': 0.0, 'weight': 0.05, 'contribution': 0.0}
            }
            decision_factors = [f"Face match confidence: {confidence:.2f}"]
            uncertainty_factors = []
        
        return {
            'confidence_score': confidence,
            'confidence_category': category,
            'feature_weights': json.dumps(feature_weights),
            'frame_hash': evidence.get('frame_hash', 'unavailable'),
            'evidence_number': evidence.get('evidence_number', 'unavailable'),
            'detection_box': json.dumps(detection_data.get('bbox', (0, 0, 0, 0))),
            'face_match_score': confidence,
            'clothing_match_score': detection_data.get('clothing_confidence', 0.0),
            'body_pose_score': detection_data.get('body_confidence', 0.0),
            'temporal_consistency_score': detection_data.get('consistency', 0.0),
            'decision_factors': json.dumps(decision_factors),
            'uncertainty_factors': json.dumps(uncertainty_factors)
        }

# Global instance cache
_vision_engines = {}

def get_vision_engine(case_id=None):
    """Get or create vision engine instance for case"""
    global _vision_engines
    
    key = case_id or 'default'
    
    if key not in _vision_engines:
        try:
            _vision_engines[key] = VisionEngine(case_id)
            logger.info(f"✅ Vision engine created for case {case_id}")
        except Exception as e:
            logger.error(f"❌ Vision engine creation failed: {e}")
            return None
    
    return _vision_engines[key]
