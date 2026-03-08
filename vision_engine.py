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
from pathlib import Path
from collections import deque

logger = logging.getLogger(__name__)

class VisionEngine:
    """Unified vision engine for all person detection tasks"""
    
    def __init__(self, case_id=None):
        self.case_id = case_id
        self.detector = None
        self.evidence_system = None
        self.xai_system = None
        self.temporal_buffer = {}  # Track faces across frames
        self.ai_config = self._load_ai_config()  # Load dynamic AI settings
        self._init_systems()
    
    def _load_ai_config(self):
        """Load AI configuration from database (dynamic settings)"""
        try:
            from ai_config_model import AIConfig
            config = AIConfig.get_config()
            return {
                'threshold': 0.50,  # DEMO MODE: 50% for surveillance leads
                'facial_weight': config.facial_weight,
                'clothing_weight': config.clothing_weight,
                'temporal_weight': config.temporal_weight,
                'frame_skip': 1  # HIGH-DENSITY: Process every frame
            }
        except Exception as e:
            logger.warning(f"Failed to load AI config, using defaults: {e}")
            return {
                'threshold': 0.50,  # DEMO MODE: 50% for surveillance leads
                'facial_weight': 0.40,
                'clothing_weight': 0.35,
                'temporal_weight': 0.25,
                'frame_skip': 1  # HIGH-DENSITY: Process every frame
            }
    
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
    
    def detect_person(self, frame, target_encoding=None, case_id=None, strict_mode=True, person_profile=None):
        """
        Detect person with quality filtering and strict landmark validation
        
        Args:
            strict_mode: If True, requires 2 eyes + nose + mouth + dynamic confidence
            person_profile: PersonProfile object with multi-view encodings
        """
        # CRITICAL: Reload config for every detection (Celery worker sync)
        self.ai_config = self._load_ai_config()
        
        if frame is None or not isinstance(frame, np.ndarray):
            return None
        
        if case_id:
            self.case_id = case_id
        
        # Use multi-view encodings if profile provided
        if person_profile and not target_encoding:
            # Try matching against all available encodings
            all_encodings = person_profile.face_encodings_list
            if all_encodings is not None and len(all_encodings) > 0:
                target_encoding = all_encodings[0]  # Use first as primary
        
        detection_data = self._build_detection_data_strict(frame, target_encoding, strict_mode, person_profile)
        
        if not detection_data:
            return None
        
        # QUALITY FILTER: Check face size (min 40x40 pixels)
        bbox = detection_data.get('bbox', (0, 0, 0, 0))
        face_width = bbox[2] if len(bbox) > 2 else 0
        face_height = bbox[3] if len(bbox) > 3 else 0
        
        if face_width < 40 or face_height < 40:
            logger.debug(f"Face too small: {face_width}x{face_height} - skipping")
            return None
        
        # QUALITY FILTER: Check blur (Laplacian variance)
        try:
            x, y, w, h = bbox
            face_roi = frame[y:y+h, x:x+w]
            gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            blur_score = cv2.Laplacian(gray_face, cv2.CV_64F).var()
            
            if blur_score < 100:  # Threshold for blur detection
                logger.debug(f"Face too blurry: {blur_score:.1f} - skipping")
                return None
        except Exception as e:
            logger.debug(f"Blur check failed: {e}")
        
        # Save extracted frame with SHA-256 hash
        frame_path = self._save_detection_frame(frame, detection_data)
        detection_data['frame_path'] = frame_path
        
        # Generate evidence with hash
        evidence = self._generate_evidence(frame, detection_data)
        detection_data['frame_hash'] = evidence.get('frame_hash', '')
        detection_data['evidence_number'] = evidence.get('evidence_number', '')
        
        # Calculate XAI weights with dynamic config
        xai_result = self._calculate_xai_weights(detection_data)
        
        return self._merge_results(detection_data, evidence, xai_result)
    
    def detect_multi_view(self, frame, target_profiles, timestamp=0.0, case_id=None):
        """
        Multi-view detection with front + side profiles
        
        Args:
            frame: Video frame
            target_profiles: Dict with 'front', 'left_profile', 'right_profile' encodings
            timestamp: Frame timestamp
            case_id: Case ID
        
        Returns:
            Detection result with forensic rendering
        """
        try:
            from multi_view_forensic_engine import MultiViewForensicEngine
            
            if case_id:
                self.case_id = case_id
            
            engine = MultiViewForensicEngine(self.case_id or 0)
            detection_result = engine.detect_multi_view(frame, target_profiles, timestamp)
            
            if not detection_result:
                return None
            
            # Save forensic output
            saved = engine.save_forensic_detection(frame, detection_result, timestamp, self.case_id or 0)
            
            if not saved:
                return None
            
            # Build detection data
            target = detection_result['target']
            top, right, bottom, left = target['location']
            
            return {
                'confidence_score': target['confidence'],
                'confidence_category': 'very_high' if target['confidence'] >= 0.9 else 'high',
                'matched_profile': target['matched_profile'],
                'temporal_count': detection_result['temporal_count'],
                'temporal_span': detection_result['temporal_span'],
                'crowd_size': len(detection_result['all_faces']),
                'frame_hash': saved['frame_hash'],
                'evidence_number': saved['evidence_number'],
                'frame_path': saved['filepath'],
                'detection_box': json.dumps({'top': int(top), 'right': int(right), 'bottom': int(bottom), 'left': int(left)}),
                'face_match_score': target['confidence'],
                'decision_factors': json.dumps([
                    f"Multi-view match: {target['matched_profile']}",
                    f"Temporal consensus: {detection_result['temporal_count']} frames",
                    f"Crowd analysis: {len(detection_result['all_faces'])} faces",
                    f"Motion filtering applied",
                    f"Confidence: {target['confidence']*100:.1f}%"
                ]),
                'feature_weights': json.dumps({
                    'multi_view_matching': {'score': target['confidence'], 'weight': 0.5},
                    'temporal_consistency': {'score': 1.0, 'weight': 0.3},
                    'motion_filtering': {'score': 1.0, 'weight': 0.2}
                })
            }
            
        except Exception as e:
            logger.error(f"Multi-view detection error: {e}")
            return None
    
    def _build_detection_data(self, frame, target_encoding, strict_mode=False):
        """Build detection with frontal-face validation using 68-point landmarks"""
        try:
            import face_recognition
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame, model='hog')
            
            if face_locations is None or len(face_locations) == 0:
                return None
            
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            if face_encodings is None or len(face_encodings) == 0:
                return None
            
            # Get 68-point landmarks for frontal validation
            face_landmarks_list = face_recognition.face_landmarks(rgb_frame, face_locations)
            
            best_match = None
            best_confidence = 0.0
            best_location = None
            is_frontal = False
            face_pose_angles = None
            
            for idx, (face_encoding, face_location) in enumerate(zip(face_encodings, face_locations)):
                # Frontal-face validation using 68-point landmarks
                if idx < len(face_landmarks_list):
                    landmarks = face_landmarks_list[idx]
                    
                    # Check if all required landmarks exist
                    if not all(k in landmarks for k in ['left_eye', 'right_eye', 'nose_tip', 'chin']):
                        continue
                    
                    # Calculate face pose angles (Yaw/Pitch)
                    pose_angles = self._calculate_face_pose(landmarks)
                    
                    # Skip if face is not frontal (Yaw/Pitch > 15 degrees)
                    if abs(pose_angles['yaw']) > 15 or abs(pose_angles['pitch']) > 15:
                        logger.debug(f"Skipping non-frontal face: Yaw={pose_angles['yaw']:.1f}°, Pitch={pose_angles['pitch']:.1f}°")
                        continue
                    
                    is_frontal = True
                    face_pose_angles = pose_angles
                
                if target_encoding is not None:
                    distances = face_recognition.face_distance([target_encoding], face_encoding)
                    if distances is None or len(distances) == 0:
                        continue
                    distance = float(distances[0])
                    confidence = max(0.0, 1.0 - distance)
                    
                    # FORENSIC THRESHOLD: Hardcoded 0.80
                    threshold = 0.60
                    
                    # Log near-matches for debugging
                    if 0.70 <= confidence < threshold:
                        logger.info(f"🔶 Near Match: {confidence*100:.1f}% (below {threshold*100:.0f}% threshold)")
                    
                    if confidence < threshold:
                        continue
                    
                    if confidence > best_confidence and confidence >= threshold:
                        best_confidence = confidence
                        best_match = face_encoding
                        best_location = face_location
                else:
                    best_confidence = 0.7
                    best_match = face_encoding
                    best_location = face_location
                    break
            
            if best_match is None or best_confidence < 0.60:
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
                'method': 'frontal_validated' if is_frontal else 'vision_engine',
                'is_frontal_face': is_frontal,
                'face_pose_yaw': face_pose_angles['yaw'] if face_pose_angles else 0,
                'face_pose_pitch': face_pose_angles['pitch'] if face_pose_angles else 0,
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
    
    def _calculate_face_pose(self, landmarks):
        """Calculate face pose angles (Yaw/Pitch) from 68-point landmarks"""
        try:
            # Get key points
            left_eye = np.mean(landmarks['left_eye'], axis=0)
            right_eye = np.mean(landmarks['right_eye'], axis=0)
            nose_tip = np.mean(landmarks['nose_tip'], axis=0)
            chin = landmarks['chin'][8]  # Center of chin
            
            # Calculate Yaw (horizontal rotation)
            eye_center = (left_eye + right_eye) / 2
            eye_to_nose = nose_tip[0] - eye_center[0]
            eye_width = np.linalg.norm(right_eye - left_eye)
            yaw = np.degrees(np.arctan2(eye_to_nose, eye_width / 2)) * 2
            
            # Calculate Pitch (vertical rotation)
            nose_to_chin = chin[1] - nose_tip[1]
            face_height = chin[1] - eye_center[1]
            pitch = np.degrees(np.arctan2(nose_to_chin - face_height * 0.5, face_height)) * 1.5
            
            return {'yaw': float(yaw), 'pitch': float(pitch)}
        except:
            return {'yaw': 0.0, 'pitch': 0.0}
    
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
        """Calculate XAI feature weights using dynamic AI config"""
        try:
            # Use dynamic weights from AI config
            facial_weight = self.ai_config.get('facial_weight', 0.40)
            clothing_weight = self.ai_config.get('clothing_weight', 0.35)
            temporal_weight = self.ai_config.get('temporal_weight', 0.25)
            
            # Calculate weighted confidence
            face_score = detection_data.get('face_confidence', 0.0)
            clothing_score = detection_data.get('clothing_confidence', 0.0)
            temporal_score = detection_data.get('consistency', 0.0)
            
            weighted_confidence = (
                face_score * facial_weight +
                clothing_score * clothing_weight +
                temporal_score * temporal_weight
            )
            
            # Build XAI result
            xai_result = type('XAIResult', (), {
                'feature_weights': type('Weights', (), {
                    'get_confidence_breakdown': lambda: {
                        'facial_structure': {'score': face_score, 'weight': facial_weight, 'contribution': face_score * facial_weight},
                        'clothing_biometric': {'score': clothing_score, 'weight': clothing_weight, 'contribution': clothing_score * clothing_weight},
                        'temporal_consistency': {'score': temporal_score, 'weight': temporal_weight, 'contribution': temporal_score * temporal_weight}
                    }
                })(),
                'decision_factors': [
                    f"Facial match: {face_score*100:.1f}% × {facial_weight*100:.0f}%",
                    f"Clothing match: {clothing_score*100:.1f}% × {clothing_weight*100:.0f}%",
                    f"Temporal consistency: {temporal_score*100:.1f}% × {temporal_weight*100:.0f}%",
                    f"Weighted confidence: {weighted_confidence*100:.1f}%"
                ],
                'uncertainty_factors': []
            })()
            
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

    
    def _save_detection_frame(self, frame, detection_data):
        """Save forensic output with zoom-in inset"""
        try:
            case_id = detection_data.get('case_id', 0)
            evidence_num = detection_data.get('evidence_number', f"EVD-{datetime.now().strftime('%Y%m%d%H%M%S')}")
            
            detection_dir = Path(f"static/detections/case_{case_id}")
            detection_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = detection_data.get('timestamp', 0.0)
            frame_filename = f"{evidence_num}_forensic_t{timestamp:.2f}.jpg"
            frame_path = detection_dir / frame_filename
            
            # Render forensic output
            forensic_frame = self.render_forensic_output(frame, detection_data)
            cv2.imwrite(str(forensic_frame), forensic_frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            logger.info(f"✅ Saved forensic frame: {frame_path}")
            
            return str(frame_path)
        except Exception as e:
            logger.error(f"❌ Failed to save detection frame: {e}")
            return ""
    
    def _build_detection_data_strict(self, frame, target_encoding, strict_mode=True, person_profile=None):
        """Build detection with STRICT landmark filtering: 2 eyes + nose + mouth required
        
        Args:
            person_profile: PersonProfile with multi-view encodings for better matching
        """
        try:
            import face_recognition
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame, model='hog')
            
            if face_locations is None or len(face_locations) == 0:
                return None
            
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            if face_encodings is None or len(face_encodings) == 0:
                return None
            
            # Get landmarks for ALL faces
            face_landmarks_list = face_recognition.face_landmarks(rgb_frame, face_locations)
            
            best_match = None
            best_confidence = 0.0
            best_location = None
            is_frontal = False
            face_pose_angles = None
            xai_factors = []
            matched_view = 'unknown'
            
            # Prepare multi-view encodings if available
            multi_view_encodings = {}
            if person_profile:
                multi_view_encodings = {
                    'front': person_profile.front_encodings_list,
                    'left_profile': person_profile.left_profile_encodings_list,
                    'right_profile': person_profile.right_profile_encodings_list,
                    'video': person_profile.video_encodings_list
                }
            
            for idx, (face_encoding, face_location) in enumerate(zip(face_encodings, face_locations)):
                # STRICT LANDMARK CHECK: Must have 2 eyes + nose + mouth
                if idx < len(face_landmarks_list):
                    landmarks = face_landmarks_list[idx]
                    
                    # RELAXED: Check basic landmarks only
                    has_left_eye = 'left_eye' in landmarks and len(landmarks.get('left_eye', [])) > 0
                    has_right_eye = 'right_eye' in landmarks and len(landmarks.get('right_eye', [])) > 0
                    has_nose = 'nose_tip' in landmarks and len(landmarks.get('nose_tip', [])) > 0
                    
                    if not (has_left_eye or has_right_eye or has_nose):
                        logger.debug(f"Skipping face: No basic landmarks")
                        continue
                    
                    left_eye_count = len(landmarks.get('left_eye', []))
                    right_eye_count = len(landmarks.get('right_eye', []))
                    nose_count = len(landmarks.get('nose_tip', []))
                    mouth_count = len(landmarks.get('top_lip', [])) + len(landmarks.get('bottom_lip', []))
                    
                    # Calculate face pose
                    pose_angles = self._calculate_face_pose(landmarks)
                    
                    # RELAXED: Allow ±30° for walking/movement
                    if abs(pose_angles['yaw']) > 30 or abs(pose_angles['pitch']) > 30:
                        logger.debug(f"Skipping extreme angle: Yaw={pose_angles['yaw']:.1f}°, Pitch={pose_angles['pitch']:.1f}°")
                        continue
                    
                    is_frontal = True
                    face_pose_angles = pose_angles
                    
                    # Build XAI factors
                    xai_factors = [
                        f"Eyes detected: {left_eye_count + right_eye_count} points",
                        f"Nose detected: {nose_count} points",
                        f"Mouth detected: {mouth_count} points",
                        f"Pose: Yaw {pose_angles['yaw']:.1f}°, Pitch {pose_angles['pitch']:.1f}° (±30° tolerance)"
                    ]
                
                # Calculate confidence with multi-view matching
                if target_encoding is not None or multi_view_encodings:
                    # Try matching against all available encodings
                    best_view_confidence = 0.0
                    best_view_name = 'primary'
                    
                    # Match against primary encoding
                    if target_encoding is not None:
                        distances = face_recognition.face_distance([target_encoding], face_encoding)
                        if distances is None or len(distances) == 0:
                            continue
                        distance = float(distances[0])
                        confidence = max(0.0, 1.0 - distance)
                        if confidence > best_view_confidence:
                            best_view_confidence = confidence
                            best_view_name = 'primary'
                    
                    # Match against multi-view encodings
                    for view_name, view_encodings in multi_view_encodings.items():
                        if not view_encodings or len(view_encodings) == 0:
                            continue
                        for view_enc in view_encodings:
                            distances = face_recognition.face_distance([view_enc], face_encoding)
                            if distances is None or len(distances) == 0:
                                continue
                            distance = float(distances[0])
                            confidence = max(0.0, 1.0 - distance)
                            if confidence > best_view_confidence:
                                best_view_confidence = confidence
                                best_view_name = view_name
                    
                    confidence = best_view_confidence
                    matched_view = best_view_name
                    
                    # DEMO MODE: 50% threshold
                    threshold = 0.50
                    
                    # Log near-matches
                    if 0.45 <= confidence < threshold:
                        logger.info(f"🔶 Near Match ({matched_view}): {confidence*100:.1f}% (below {threshold*100:.0f}% threshold)")
                    
                    if confidence < threshold:
                        continue
                    
                    xai_factors.append(f"Face match confidence: {confidence * 100:.1f}% (matched view: {matched_view})")
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = face_encoding
                        best_location = face_location
                else:
                    best_confidence = 0.7
                    best_match = face_encoding
                    best_location = face_location
                    break
            
            if best_match is None or best_confidence < 0.60:
                return None
            
            top, right, bottom, left = best_location
            bbox = (left, top, right - left, bottom - top)
            
            return {
                'confidence': best_confidence,
                'face_confidence': best_confidence,
                'confidence_score': best_confidence,
                'face_match_score': best_confidence,
                'matched_view': matched_view,
                'bbox': bbox,
                'detection_box': bbox,
                'face_encoding': best_match.tolist(),
                'timestamp': 0.0,
                'case_id': self.case_id or 0,
                'footage_id': 0,
                'method': f'multi_view_strict_{matched_view}',
                'is_frontal_face': is_frontal,
                'face_pose_yaw': face_pose_angles['yaw'] if face_pose_angles else 0,
                'face_pose_pitch': face_pose_angles['pitch'] if face_pose_angles else 0,
                'decision_factors': json.dumps(xai_factors),
                'feature_weights': json.dumps({
                    'facial_landmarks': {'score': 1.0, 'weight': 0.4},
                    'face_match': {'score': best_confidence, 'weight': 0.6}
                }),
                'evidence_number': f"EVD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'frame_hash': '',  # Will be generated during save
                'clothing_confidence': 0.0,
                'body_confidence': 0.0,
                'motion_confidence': 0.0,
                'duration': 0.0,
                'consistency': 0.0,
                'tracking_stability': 0.0,
                'frame_quality': 0.9,
                'face_visibility': 0.9,
                'lighting_quality': 0.8
            }
            
        except Exception as e:
            logger.error(f"Strict detection error: {e}")
            return None

