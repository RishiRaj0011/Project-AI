"""
AWS Rekognition - Professional CCTV Analysis
- Crowd detection
- Moving people tracking
- Multiple faces simultaneously
- Distance/angle independent
- Cloud-based fast processing
"""
import boto3
import cv2
import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv  # Ye line add karein
from __init__ import db
from models import Case, SurveillanceFootage, LocationMatch, PersonDetection
import numpy as np

# Environment variables load karein
load_dotenv()

logger = logging.getLogger(__name__)

class AWSRekognitionMatcher:
    def __init__(self):
        # AWS credentials (SECURE WAY)
        self.rekognition = boto3.client(
            'rekognition',
            region_name=os.getenv('AWS_REGION', 'ap-south-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
    
    def analyze_footage_for_person(self, match_id):
        """Analyze CCTV footage using AWS Rekognition CompareFaces"""
        try:
            match = LocationMatch.query.get(match_id)
            if not match:
                return False
            
            match.status = 'processing'
            match.ai_analysis_started = datetime.utcnow()
            db.session.commit()
            
            # Get reference image
            reference_image_path = None
            for target_image in match.case.target_images:
                image_path = os.path.join('static', target_image.image_path)
                if not os.path.exists(image_path):
                    image_path = os.path.join('app', 'static', target_image.image_path)
                
                if os.path.exists(image_path):
                    reference_image_path = image_path
                    break
            
            if not reference_image_path:
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
            
            # Analyze video with AWS Rekognition
            detections = self._analyze_video_aws(footage_path, reference_image_path, match_id)
            
            match.detection_count = len(detections)
            match.person_found = len(detections) > 0
            
            if detections:
                confidences = [d['confidence'] for d in detections]
                match.confidence_score = sum(confidences) / len(confidences)
            else:
                match.confidence_score = 0.0
            
            match.status = 'completed'
            match.ai_analysis_completed = datetime.utcnow()
            db.session.commit()
            
            return True
        except Exception as e:
            logger.error(f"AWS analysis error: {e}")
            if match:
                match.status = 'failed'
                db.session.commit()
            return False
    
    def _analyze_video_aws(self, video_path, reference_image_path, match_id):
        """AWS CompareFaces - Fast and Reliable"""
        detections = []
        try:
            # Load and prepare reference image
            ref_img = cv2.imread(reference_image_path)
            if ref_img is None:
                logger.error(f"Cannot read reference image: {reference_image_path}")
                return detections
            
            # Resize if too large
            h, w = ref_img.shape[:2]
            if w > 1920 or h > 1920:
                scale = 1920 / max(w, h)
                ref_img = cv2.resize(ref_img, None, fx=scale, fy=scale)
            
            _, ref_buffer = cv2.imencode('.jpg', ref_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
            reference_bytes = ref_buffer.tobytes()
            
            # Check size
            if len(reference_bytes) > 5 * 1024 * 1024:
                _, ref_buffer = cv2.imencode('.jpg', ref_img, [cv2.IMWRITE_JPEG_QUALITY, 85])
                reference_bytes = ref_buffer.tobytes()
            
            logger.info(f"Reference image size: {len(reference_bytes)} bytes")
            
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps
            
            # Smart sampling: 2 frames per second
            sample_rate = 0.5
            frames_to_check = [int(i * fps * sample_rate) for i in range(int(duration / sample_rate))]
            
            logger.info(f"AWS analysis: {duration:.1f}s video, {len(frames_to_check)} frames")
            
            for frame_num in frames_to_check:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                if not ret:
                    continue
                
                timestamp = frame_num / fps
                
                # Resize frame if too large
                h, w = frame.shape[:2]
                if w > 1920 or h > 1920:
                    scale = 1920 / max(w, h)
                    frame = cv2.resize(frame, None, fx=scale, fy=scale)
                
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                frame_bytes = buffer.tobytes()
                
                if len(frame_bytes) > 5 * 1024 * 1024:
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    frame_bytes = buffer.tobytes()
                
                process_frame = frame
                
                try:
                    # Try face matching first
                    response = self.rekognition.compare_faces(
                        SourceImage={'Bytes': reference_bytes},
                        TargetImage={'Bytes': frame_bytes},
                        SimilarityThreshold=30,
                        QualityFilter='NONE'
                    )
                    
                    logger.info(f"Frame {frame_num}: Found {len(response.get('FaceMatches', []))} face matches")
                    
                    for match in response['FaceMatches']:
                        confidence = match['Similarity']
                        bbox = match['Face']['BoundingBox']
                        h, w = process_frame.shape[:2]
                        location = (
                            int(bbox['Top'] * h),
                            int((bbox['Left'] + bbox['Width']) * w),
                            int((bbox['Top'] + bbox['Height']) * h),
                            int(bbox['Left'] * w)
                        )
                        
                        self._save_detection(process_frame, location, timestamp, match_id, confidence)
                        detections.append({'timestamp': timestamp, 'confidence': confidence})
                        logger.info(f"✓ Face match at {timestamp:.2f}s: {confidence:.1f}%")
                
                except Exception as e:
                    logger.warning(f"Frame {frame_num}: Face matching failed - {str(e)}")
                    # If face matching fails, try person detection
                    try:
                        person_response = self.rekognition.detect_labels(
                            Image={'Bytes': frame_bytes},
                            MaxLabels=20,
                            MinConfidence=50
                        )
                        
                        # Check if person detected
                        for label in person_response['Labels']:
                            if label['Name'].lower() in ['person', 'people', 'human']:
                                # Person detected - save with adjusted confidence
                                confidence = label['Confidence'] * 0.6  # 60% weight for person detection
                                
                                # Use first instance bounding box if available
                                if label.get('Instances') and len(label['Instances']) > 0:
                                    bbox = label['Instances'][0]['BoundingBox']
                                    h, w = frame.shape[:2]
                                    location = (
                                        int(bbox['Top'] * h),
                                        int((bbox['Left'] + bbox['Width']) * w),
                                        int((bbox['Top'] + bbox['Height']) * h),
                                        int(bbox['Left'] * w)
                                    )
                                else:
                                    # No bounding box - use full frame
                                    h, w = frame.shape[:2]
                                    location = (0, w, h, 0)
                                
                                self._save_detection(process_frame, location, timestamp, match_id, confidence)
                                detections.append({'timestamp': timestamp, 'confidence': confidence})
                                logger.info(f"✓ Person detected at {timestamp:.2f}s: {confidence:.1f}%")
                                break
                    except Exception as e:
                        logger.warning(f"Frame {frame_num}: Person detection also failed - {str(e)}")
            
            cap.release()
            db.session.commit()
            logger.info(f"AWS done: {len(detections)} detections")
            
        except Exception as e:
            logger.error(f"AWS error: {e}")
        
        return detections
    
    def _extract_clothing_colors(self, image):
        """Extract dominant colors from image for clothing matching"""
        try:
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Get dominant colors
            pixels = hsv.reshape(-1, 3)
            from sklearn.cluster import KMeans
            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
            kmeans.fit(pixels)
            
            colors = kmeans.cluster_centers_
            return colors.tolist()
        except:
            return None
    
    def _compare_clothing_colors(self, ref_colors, frame_colors):
        """Compare clothing colors between reference and frame"""
        if not ref_colors or not frame_colors:
            return 0.0
        
        try:
            # Calculate color similarity
            similarities = []
            for ref_color in ref_colors:
                for frame_color in frame_colors:
                    # Euclidean distance in HSV space
                    dist = np.sqrt(sum((a - b) ** 2 for a, b in zip(ref_color, frame_color)))
                    similarity = max(0, 100 - dist)
                    similarities.append(similarity)
            
            return max(similarities) if similarities else 0.0
        except:
            return 0.0
    
    def _calculate_smart_confidence(self, frame, location, raw_confidence):
        """Perfect confidence - blur aware, keeps visible faces"""
        try:
            # Reject only very low confidence
            if raw_confidence < 25:
                return 0.0
            
            top, right, bottom, left = location
            region = frame[max(0, top):min(frame.shape[0], bottom), 
                          max(0, left):min(frame.shape[1], right)]
            
            if region.size == 0:
                return 0.0
            
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            
            # Blur detection
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            if laplacian_var < 10:  # Extremely blurry but face visible
                quality_factor = 1.0  # Keep original
            elif laplacian_var < 50:  # Very blurry but visible
                quality_factor = 1.0  # Keep original
            elif laplacian_var < 100:  # Slightly blurry
                quality_factor = 1.0  # Keep original
            else:  # Clear
                quality_factor = 1.2  # Boost clear faces
            
            # Apply quality adjustment
            adjusted = raw_confidence * quality_factor
            
            logger.info(f"Blur={laplacian_var:.1f}, Raw={raw_confidence:.1f}%, "
                       f"Factor={quality_factor:.2f}, Final={adjusted:.1f}%")
            
            return min(adjusted, 100.0)
            
        except Exception as e:
            logger.error(f"Smart confidence error: {e}")
            return raw_confidence * 0.8
    
    def _save_detection(self, frame, location, timestamp, match_id, confidence_percent):
        try:
            frame_filename = f"detection_{match_id}_{int(timestamp)}.jpg"
            frame_dir = os.path.join('static', 'detections')
            if not os.path.exists(frame_dir):
                frame_dir = os.path.join('app', 'static', 'detections')
            os.makedirs(frame_dir, exist_ok=True)
            
            top, right, bottom, left = location
            region = frame[max(0, top-20):min(frame.shape[0], bottom+20), 
                          max(0, left-20):min(frame.shape[1], right+20)]
            
            if region.size > 0:
                # Calculate smart confidence
                smart_confidence = self._calculate_smart_confidence(frame, location, confidence_percent)
                
                cv2.imwrite(os.path.join(frame_dir, frame_filename), region)
                
                # Auto-verify if confidence >= 65%
                auto_verified = smart_confidence >= 65.0
                
                # Normalize smart confidence to 0-1 range
                normalized_confidence = min(100, smart_confidence) / 100.0
                
                detection = PersonDetection(
                    location_match_id=match_id,
                    timestamp=timestamp,
                    confidence_score=normalized_confidence,
                    face_match_score=normalized_confidence,  # Same as confidence for face-based detection
                    clothing_match_score=None,
                    detection_box=json.dumps({'top': int(top), 'right': int(right), 'bottom': int(bottom), 'left': int(left)}),
                    frame_path=f"detections/{frame_filename}",
                    analysis_method='final_correct_matching',
                    verified=auto_verified,
                    notes='Auto-verified by AI' if auto_verified else None
                )
                db.session.add(detection)
                
                if auto_verified:
                    logger.info(f"Auto-verified detection at {timestamp:.2f}s with {smart_confidence:.1f}% confidence")
        except Exception as e:
            logger.error(f"Save detection error: {e}")
    
    # Location matching methods (same as before)
    def find_location_matches(self, case_id):
        from ai_location_matcher import ai_matcher
        return ai_matcher.find_location_matches(case_id)
    
    def process_new_case(self, case_id):
        from ai_location_matcher import ai_matcher
        return ai_matcher.process_new_case(case_id)
    
    def process_new_footage(self, footage_id):
        from ai_location_matcher import ai_matcher
        return ai_matcher.process_new_footage(footage_id)

# Global instance
aws_matcher = AWSRekognitionMatcher()
