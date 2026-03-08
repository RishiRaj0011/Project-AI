"""
Advanced CCTV Forensic Vision Engine
Handles crowds, movement, low-light with forensic zoom-in output
"""
import cv2
import numpy as np
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from collections import deque

logger = logging.getLogger(__name__)

class ForensicVisionEngine:
    """Advanced CCTV forensic analysis with zoom-in inset rendering"""
    
    def __init__(self, case_id=None):
        self.case_id = case_id
        self.temporal_buffer = {}  # Track faces across frames for temporal smoothing
        self.frame_history = 10  # Confirm match over 10 frames
    
    def _enhance_low_light(self, frame):
        """Apply CLAHE for low-light enhancement"""
        try:
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            enhanced = cv2.merge([l, a, b])
            return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        except:
            return frame
    
    def _get_face_id(self, location):
        """Generate face ID from location for temporal tracking"""
        top, right, bottom, left = location
        return f"{left}_{top}_{right}_{bottom}"
    
    def _confirm_temporal_consistency(self, face_id, confidence):
        """Temporal smoothing: confirm match over 5-10 frames"""
        if face_id not in self.temporal_buffer:
            self.temporal_buffer[face_id] = deque(maxlen=self.frame_history)
        
        self.temporal_buffer[face_id].append(confidence)
        
        # Require at least 5 consistent frames with avg confidence >= 0.80
        if len(self.temporal_buffer[face_id]) >= 5:
            avg_confidence = sum(self.temporal_buffer[face_id]) / len(self.temporal_buffer[face_id])
            return avg_confidence >= 0.80
        
        return False
    
    def detect_in_crowd(self, frame, target_encoding):
        """Multi-scale detection for crowds and distant faces"""
        try:
            import face_recognition
            
            # Low-light enhancement
            enhanced = self._enhance_low_light(frame)
            rgb_frame = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
            
            # Multi-scale detection (CNN model, 2x upsampling for small faces)
            face_locations = face_recognition.face_locations(
                rgb_frame, 
                model='cnn', 
                number_of_times_to_upsample=2
            )
            
            if face_locations is None or len(face_locations) == 0:
                return None
            
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            face_landmarks_list = face_recognition.face_landmarks(rgb_frame, face_locations)
            
            all_faces = []
            target_match = None
            
            for idx, (encoding, location) in enumerate(zip(face_encodings, face_locations)):
                face_data = {'location': location, 'encoding': encoding}
                
                # Strict frontal validation
                if idx < len(face_landmarks_list):
                    landmarks = face_landmarks_list[idx]
                    
                    if not all(k in landmarks for k in ['left_eye', 'right_eye', 'nose_tip', 'top_lip', 'bottom_lip']):
                        continue
                    
                    # Landmark quality check
                    if (len(landmarks.get('left_eye', [])) < 4 or 
                        len(landmarks.get('right_eye', [])) < 4 or
                        len(landmarks.get('nose_tip', [])) < 3 or
                        len(landmarks.get('top_lip', [])) + len(landmarks.get('bottom_lip', [])) < 10):
                        continue
                    
                    # Pose check: ±15° only
                    pose = self._calculate_pose(landmarks)
                    if abs(pose['yaw']) > 15 or abs(pose['pitch']) > 15:
                        continue
                    
                    face_data['landmarks'] = landmarks
                    face_data['pose'] = pose
                    face_data['is_frontal'] = True
                
                all_faces.append(face_data)
                
                # Match against target
                if target_encoding is not None and 'is_frontal' in face_data:
                    distances = face_recognition.face_distance([target_encoding], encoding)
                    if distances is None or len(distances) == 0:
                        continue
                    distance = float(distances[0])
                    confidence = max(0.0, 1.0 - distance)
                    
                    # Log near-matches for debugging
                    if 0.70 <= confidence < 0.80:
                        logger.info(f"🔶 Near Match: {confidence*100:.1f}% (below 80% threshold)")
                    
                    if confidence >= 0.80:
                        face_id = self._get_face_id(location)
                        if self._confirm_temporal_consistency(face_id, confidence):
                            if not target_match or confidence > target_match['confidence']:
                                target_match = {
                                    'location': location,
                                    'confidence': confidence,
                                    'landmarks': landmarks,
                                    'encoding': encoding
                                }
            
            if target_match:
                return {
                    'target': target_match,
                    'all_faces': all_faces,
                    'crowd_size': len(all_faces)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Crowd detection error: {e}")
            return None
    
    def _calculate_pose(self, landmarks):
        """Calculate face pose angles"""
        try:
            left_eye = np.mean(landmarks['left_eye'], axis=0)
            right_eye = np.mean(landmarks['right_eye'], axis=0)
            nose_tip = np.mean(landmarks['nose_tip'], axis=0)
            chin = landmarks['chin'][8]
            
            eye_center = (left_eye + right_eye) / 2
            eye_to_nose = nose_tip[0] - eye_center[0]
            eye_width = np.linalg.norm(right_eye - left_eye)
            yaw = np.degrees(np.arctan2(eye_to_nose, eye_width / 2)) * 2
            
            nose_to_chin = chin[1] - nose_tip[1]
            face_height = chin[1] - eye_center[1]
            pitch = np.degrees(np.arctan2(nose_to_chin - face_height * 0.5, face_height)) * 1.5
            
            return {'yaw': float(yaw), 'pitch': float(pitch)}
        except:
            return {'yaw': 0.0, 'pitch': 0.0}
    
    def render_forensic_output(self, frame, detection_result):
        """Render CCTV-style forensic output with zoom-in inset"""
        try:
            output = frame.copy()
            h, w = output.shape[:2]
            
            # Security camera aesthetic: muted colors + grain
            output = cv2.addWeighted(output, 0.85, np.zeros_like(output), 0.15, 0)
            noise = np.random.randint(-10, 10, output.shape, dtype=np.int16)
            output = np.clip(output.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            
            target = detection_result['target']
            all_faces = detection_result.get('all_faces', [])
            
            # Draw bounding boxes for all faces in crowd
            for face in all_faces:
                top, right, bottom, left = face['location']
                cv2.rectangle(output, (left, top), (right, bottom), (255, 255, 255), 1)
            
            # Target bounding box (thicker)
            t_top, t_right, t_bottom, t_left = target['location']
            cv2.rectangle(output, (t_left, t_top), (t_right, t_bottom), (0, 255, 0), 2)
            
            # Zoom-in inset (top-right corner)
            inset_w, inset_h = int(w * 0.25), int(h * 0.25)
            inset_x, inset_y = w - inset_w - 20, 20
            
            # Extract and enhance target face
            face_region = frame[max(0, t_top-30):min(h, t_bottom+30), 
                               max(0, t_left-30):min(w, t_right+30)]
            
            if face_region.size > 0:
                # Enhance face: sharpen + brighten
                face_enhanced = cv2.detailEnhance(face_region, sigma_s=10, sigma_r=0.15)
                face_enhanced = cv2.convertScaleAbs(face_enhanced, alpha=1.2, beta=20)
                
                # Resize to inset
                face_resized = cv2.resize(face_enhanced, (inset_w - 10, inset_h - 10))
                
                # Draw inset background
                cv2.rectangle(output, (inset_x, inset_y), 
                            (inset_x + inset_w, inset_y + inset_h), (0, 0, 0), -1)
                cv2.rectangle(output, (inset_x, inset_y), 
                            (inset_x + inset_w, inset_y + inset_h), (255, 255, 255), 2)
                
                # Place enhanced face
                output[inset_y+5:inset_y+5+face_resized.shape[0], 
                      inset_x+5:inset_x+5+face_resized.shape[1]] = face_resized
                
                # Connector line from target to inset
                target_center = ((t_left + t_right) // 2, (t_top + t_bottom) // 2)
                inset_corner = (inset_x, inset_y + inset_h)
                cv2.line(output, target_center, inset_corner, (255, 255, 255), 1)
                
                # Add confidence label
                conf_text = f"MATCH: {target['confidence']*100:.1f}%"
                cv2.putText(output, conf_text, (inset_x + 5, inset_y + inset_h - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Add metadata overlay
            cv2.putText(output, f"CROWD: {detection_result['crowd_size']} FACES", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(output, f"CASE: {self.case_id}", 
                       (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            return output
            
        except Exception as e:
            logger.error(f"Forensic rendering error: {e}")
            return frame
    
    def save_forensic_detection(self, frame, detection_result, timestamp, case_id):
        """Save forensic output with SHA-256 hash"""
        try:
            detection_dir = Path(f"static/detections/case_{case_id}")
            detection_dir.mkdir(parents=True, exist_ok=True)
            
            evidence_num = f"EVD-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:17]}"
            filename = f"{evidence_num}_forensic_t{timestamp:.2f}.jpg"
            filepath = detection_dir / filename
            
            # Render forensic output
            forensic_frame = self.render_forensic_output(frame, detection_result)
            cv2.imwrite(str(filepath), forensic_frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            # Generate SHA-256 hash
            frame_bytes = cv2.imencode('.jpg', forensic_frame)[1].tobytes()
            frame_hash = hashlib.sha256(frame_bytes).hexdigest()
            
            logger.info(f"✅ Saved forensic frame: {filepath}")
            
            return {
                'filepath': str(filepath),
                'frame_hash': frame_hash,
                'evidence_number': evidence_num,
                'confidence': detection_result['target']['confidence'],
                'crowd_size': detection_result['crowd_size']
            }
            
        except Exception as e:
            logger.error(f"Save forensic detection error: {e}")
            return None

# Global instance
forensic_engine = ForensicVisionEngine()
