"""
Multi-View Face Tracking with High-Precision Forensic Visualization
Handles front + side-profile encodings with professional CCTV rendering
"""
import cv2
import numpy as np
import face_recognition
import logging
import json
import hashlib
from datetime import datetime
from pathlib import Path
from collections import deque, defaultdict

logger = logging.getLogger(__name__)

class MultiViewForensicEngine:
    """Multi-view face tracking with forensic visualization"""
    
    def __init__(self, case_id):
        self.case_id = case_id
        self.MATCH_THRESHOLD = 0.50  # DEMO MODE: 50% for surveillance
        self.TEMPORAL_WINDOW = 1  # INSTANT: 1 frame detection
        self.temporal_buffer = defaultdict(lambda: deque(maxlen=15))
        self.motion_mask = None
        self.frame_history = deque(maxlen=3)
    
    def detect_multi_view(self, frame, target_profiles, timestamp=0.0):
        """
        Detect person using multiple profile encodings (Front, Left, Right)
        
        Args:
            frame: Video frame
            target_profiles: Dict with keys 'front', 'left_profile', 'right_profile'
            timestamp: Frame timestamp
        
        Returns:
            Detection result or None
        """
        # Motion blur check
        if self._has_motion_blur(frame):
            return None
        
        # Update motion mask
        self._update_motion_mask(frame)
        
        # Detect all faces in frame
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame, model='hog')
        
        if face_locations is None or len(face_locations) == 0:
            return None
        
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        face_landmarks_list = face_recognition.face_landmarks(rgb_frame, face_locations)
        
        # Scan every face in crowd
        all_faces = []
        target_match = None
        
        for idx, (encoding, location, landmarks) in enumerate(zip(face_encodings, face_locations, face_landmarks_list)):
            # Check if face is in motion area
            if not self._is_in_motion_area(location):
                continue
            
            # Multi-view voting
            match_result = self._multi_view_voting(encoding, target_profiles)
            
            face_data = {
                'location': location,
                'encoding': encoding,
                'landmarks': landmarks,
                'is_target': match_result['is_match'],
                'confidence': match_result['confidence'],
                'matched_profile': match_result['matched_profile']
            }
            
            all_faces.append(face_data)
            
            if match_result['is_match']:
                target_match = face_data
        
        if not target_match:
            return None
        
        # Temporal consensus check
        person_id = self._get_person_id(target_match['encoding'])
        self.temporal_buffer[person_id].append({
            'timestamp': timestamp,
            'confidence': target_match['confidence'],
            'location': target_match['location']
        })
        
        # Require 1+ frame (INSTANT detection)
        if len(self.temporal_buffer[person_id]) < self.TEMPORAL_WINDOW:
            logger.info(f"🔶 Temporal buffer: {len(self.temporal_buffer[person_id])}/{self.TEMPORAL_WINDOW} frames, confidence: {target_match['confidence']*100:.1f}%")
            return None
        
        # Check temporal consistency (relaxed to 5 seconds)
        recent_detections = list(self.temporal_buffer[person_id])
        time_span = recent_detections[-1]['timestamp'] - recent_detections[0]['timestamp']
        
        if time_span > 5.0:  # Relaxed from 2.0 to 5.0 seconds
            return None
        
        # Confirmed match
        return {
            'target': target_match,
            'all_faces': all_faces,
            'timestamp': timestamp,
            'temporal_count': len(recent_detections),
            'temporal_span': time_span
        }
    
    def _multi_view_voting(self, face_encoding, target_profiles):
        """
        Voting system: Match if ANY profile matches with score > 0.85
        
        Args:
            face_encoding: Detected face encoding
            target_profiles: Dict with 'front', 'left_profile', 'right_profile'
        
        Returns:
            Dict with is_match, confidence, matched_profile
        """
        best_match = {
            'is_match': False,
            'confidence': 0.0,
            'matched_profile': None
        }
        
        for profile_name, profile_encoding in target_profiles.items():
            if profile_encoding is None:
                continue
            
            distance = face_recognition.face_distance([profile_encoding], face_encoding)[0]
            confidence = max(0.0, 1.0 - distance)
            
            # Log all matches for debugging
            if confidence >= 0.50:
                logger.info(f"🔍 Face match: {profile_name} = {confidence*100:.1f}% (threshold: {self.MATCH_THRESHOLD*100:.0f}%)")
            
            if confidence > self.MATCH_THRESHOLD and confidence > best_match['confidence']:
                best_match = {
                    'is_match': True,
                    'confidence': confidence,
                    'matched_profile': profile_name
                }
        
        return best_match
    
    def _has_motion_blur(self, frame):
        """Check if frame has motion blur (Laplacian variance)"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            return laplacian_var < 100  # Threshold for blur
        except:
            return False
    
    def _update_motion_mask(self, frame):
        """Update motion mask to skip static areas"""
        try:
            self.frame_history.append(frame.copy())
            
            if len(self.frame_history) < 2:
                self.motion_mask = np.ones((frame.shape[0], frame.shape[1]), dtype=np.uint8) * 255
                return
            
            # Frame differencing
            prev_gray = cv2.cvtColor(self.frame_history[-2], cv2.COLOR_BGR2GRAY)
            curr_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            diff = cv2.absdiff(prev_gray, curr_gray)
            _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
            
            # Dilate to connect regions
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
            self.motion_mask = cv2.dilate(thresh, kernel, iterations=2)
            
        except Exception as e:
            logger.error(f"Motion mask error: {e}")
            self.motion_mask = np.ones((frame.shape[0], frame.shape[1]), dtype=np.uint8) * 255
    
    def _is_in_motion_area(self, face_location):
        """Check if face is in motion area"""
        if self.motion_mask is None:
            return True
        
        try:
            top, right, bottom, left = face_location
            roi = self.motion_mask[top:bottom, left:right]
            motion_ratio = np.sum(roi > 0) / roi.size
            return motion_ratio > 0.3  # 30% motion threshold
        except:
            return True
    
    def _get_person_id(self, encoding):
        """Generate unique person ID"""
        encoding_hash = hashlib.md5(np.array(encoding).tobytes()).hexdigest()[:8]
        return f"person_{encoding_hash}"
    
    def render_forensic_output(self, frame, detection_result):
        """
        Render professional forensic output with CCTV aesthetic
        
        Features:
        - CCTV grain and muted colors
        - White boxes on all faces
        - Bold white box on target
        - Zoom-in inset (top-right, 28% size)
        - Connecting line
        - Metadata overlay
        """
        output = frame.copy()
        h, w = output.shape[:2]
        
        # Apply CCTV aesthetic
        output = self._apply_cctv_look(output)
        
        # Draw all faces (thin white boxes)
        for face in detection_result['all_faces']:
            if not face['is_target']:
                top, right, bottom, left = face['location']
                cv2.rectangle(output, (left, top), (right, bottom), (255, 255, 255), 1)
        
        # Draw target (bold white box)
        target = detection_result['target']
        top, right, bottom, left = target['location']
        cv2.rectangle(output, (left, top), (right, bottom), (255, 255, 255), 3)
        
        # Create zoom-in inset
        inset = self._create_zoom_inset(frame, target['location'], w, h)
        
        # Position inset (top-right corner)
        inset_h, inset_w = inset.shape[:2]
        margin = 20
        x_offset = w - inset_w - margin
        y_offset = margin
        
        # Draw connecting line
        target_center = ((left + right) // 2, (top + bottom) // 2)
        inset_center = (x_offset + inset_w // 2, y_offset + inset_h // 2)
        cv2.line(output, target_center, inset_center, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Overlay inset
        output[y_offset:y_offset+inset_h, x_offset:x_offset+inset_w] = inset
        
        # Draw inset border
        cv2.rectangle(output, (x_offset, y_offset), (x_offset+inset_w, y_offset+inset_h), (255, 255, 255), 2)
        
        # Add metadata overlay
        output = self._add_metadata_overlay(output, detection_result)
        
        return output
    
    def _apply_cctv_look(self, frame):
        """Apply CCTV aesthetic: grain + muted colors"""
        # Reduce saturation
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hsv[:, :, 1] = hsv[:, :, 1] * 0.6  # Reduce saturation
        frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        # Add grain
        noise = np.random.normal(0, 8, frame.shape).astype(np.int16)
        frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        return frame
    
    def _create_zoom_inset(self, frame, location, frame_w, frame_h):
        """Create sharp, bright zoom-in inset (28% of frame width)"""
        top, right, bottom, left = location
        
        # Extract face with padding
        padding = 40
        y1 = max(0, top - padding)
        y2 = min(frame_h, bottom + padding)
        x1 = max(0, left - padding)
        x2 = min(frame_w, right + padding)
        
        face_crop = frame[y1:y2, x1:x2].copy()
        
        # Enhance brightness and sharpness
        face_crop = cv2.convertScaleAbs(face_crop, alpha=1.3, beta=20)
        
        # Sharpen
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        face_crop = cv2.filter2D(face_crop, -1, kernel)
        
        # Resize to 28% of frame width
        inset_width = int(frame_w * 0.28)
        aspect_ratio = face_crop.shape[0] / face_crop.shape[1]
        inset_height = int(inset_width * aspect_ratio)
        
        inset = cv2.resize(face_crop, (inset_width, inset_height), interpolation=cv2.INTER_CUBIC)
        
        return inset
    
    def _add_metadata_overlay(self, frame, detection_result):
        """Add metadata overlay with evidence info"""
        h, w = frame.shape[:2]
        
        # Generate evidence hash
        frame_bytes = cv2.imencode('.jpg', frame)[1].tobytes()
        evidence_hash = hashlib.sha256(frame_bytes).hexdigest()[:16]
        
        # Metadata
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        confidence = detection_result['target']['confidence']
        matched_profile = detection_result['target']['matched_profile']
        temporal_count = detection_result['temporal_count']
        
        # Draw semi-transparent overlay at bottom
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, h-80), (w, h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Add text
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, f"EVIDENCE: {evidence_hash}", (10, h-55), font, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"TIMESTAMP: {timestamp}", (10, h-35), font, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"CONFIDENCE: {confidence*100:.1f}% | PROFILE: {matched_profile.upper()} | FRAMES: {temporal_count}", 
                   (10, h-15), font, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def save_forensic_detection(self, frame, detection_result, timestamp, case_id):
        """Save forensic output with full metadata"""
        try:
            # Render forensic output
            forensic_frame = self.render_forensic_output(frame, detection_result)
            
            # Generate evidence number
            evidence_number = f"EVD-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:17]}"
            
            # Generate SHA-256 hash
            frame_bytes = cv2.imencode('.jpg', forensic_frame)[1].tobytes()
            frame_hash = hashlib.sha256(frame_bytes).hexdigest()
            
            # Save path
            detection_dir = Path(f"static/detections/case_{case_id}")
            detection_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{evidence_number}_forensic_t{timestamp:.2f}.jpg"
            filepath = detection_dir / filename
            
            cv2.imwrite(str(filepath), forensic_frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            logger.info(f"✅ Saved forensic detection: {filepath}")
            
            return {
                'filepath': str(filepath),
                'evidence_number': evidence_number,
                'frame_hash': frame_hash,
                'confidence': detection_result['target']['confidence'],
                'matched_profile': detection_result['target']['matched_profile'],
                'temporal_count': detection_result['temporal_count'],
                'crowd_size': len(detection_result['all_faces'])
            }
            
        except Exception as e:
            logger.error(f"❌ Save forensic detection error: {e}")
            return None
