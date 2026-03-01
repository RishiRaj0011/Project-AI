"""
Real-Time IP Camera Stream Processor
Zero-lag frame capture with temporal consistency and SocketIO integration
"""
import cv2
import threading
import queue
import time
import face_recognition
import numpy as np
from collections import deque, defaultdict
from datetime import datetime

class FrameBuffer:
    """Thread-safe frame buffer with minimal lag"""
    def __init__(self, maxsize=2):
        self.queue = queue.Queue(maxsize=maxsize)
        self.stopped = False
    
    def put(self, frame):
        if not self.queue.full():
            self.queue.put(frame)
        else:
            # Drop old frame, keep latest
            try:
                self.queue.get_nowait()
            except queue.Empty:
                pass
            self.queue.put(frame)
    
    def get(self):
        return self.queue.get()
    
    def empty(self):
        return self.queue.empty()
    
    def stop(self):
        self.stopped = True

class RTSPStreamCapture:
    """Threaded RTSP stream capture for zero-lag frame fetching"""
    def __init__(self, rtsp_url):
        self.rtsp_url = rtsp_url
        self.frame_buffer = FrameBuffer(maxsize=2)
        self.stopped = False
        self.capture = None
        self.thread = None
    
    def start(self):
        """Start capture thread"""
        self.capture = cv2.VideoCapture(self.rtsp_url)
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer
        
        if not self.capture.isOpened():
            raise Exception(f"Failed to open RTSP stream: {self.rtsp_url}")
        
        self.thread = threading.Thread(target=self._capture_frames, daemon=True)
        self.thread.start()
        return self
    
    def _capture_frames(self):
        """Continuously capture frames in background thread"""
        while not self.stopped:
            ret, frame = self.capture.read()
            if not ret:
                time.sleep(0.1)
                continue
            self.frame_buffer.put(frame)
    
    def read(self):
        """Get latest frame"""
        if self.frame_buffer.empty():
            return None
        return self.frame_buffer.get()
    
    def get_fps(self):
        """Get stream FPS"""
        return self.capture.get(cv2.CAP_PROP_FPS) if self.capture else 30
    
    def stop(self):
        """Stop capture thread"""
        self.stopped = True
        if self.thread:
            self.thread.join(timeout=2)
        if self.capture:
            self.capture.release()

class TemporalConsistencyTracker:
    """Track face detections across frames for temporal consistency"""
    def __init__(self, required_consecutive=3, timeout=5.0):
        self.required_consecutive = required_consecutive
        self.timeout = timeout
        self.detections = defaultdict(lambda: deque(maxlen=required_consecutive))
        self.verified_matches = set()
        self.last_seen = {}
    
    def add_detection(self, person_id, confidence, timestamp=None):
        """Add detection and check if verified"""
        timestamp = timestamp or time.time()
        
        # Clean old detections
        self._clean_old_detections(timestamp)
        
        # Add new detection
        self.detections[person_id].append({
            'confidence': confidence,
            'timestamp': timestamp
        })
        self.last_seen[person_id] = timestamp
        
        # Check if verified
        if len(self.detections[person_id]) >= self.required_consecutive:
            if person_id not in self.verified_matches:
                self.verified_matches.add(person_id)
                return True, confidence
        
        return False, confidence
    
    def _clean_old_detections(self, current_time):
        """Remove old detections beyond timeout"""
        expired = [pid for pid, ts in self.last_seen.items() 
                   if current_time - ts > self.timeout]
        for pid in expired:
            del self.detections[pid]
            del self.last_seen[pid]
            self.verified_matches.discard(pid)
    
    def reset(self):
        """Reset all tracking data"""
        self.detections.clear()
        self.verified_matches.clear()
        self.last_seen.clear()

class LiveStreamProcessor:
    """Main live stream processor with face matching"""
    def __init__(self, rtsp_url, target_encodings, socketio=None, 
                 target_fps=5, required_consecutive=3):
        self.rtsp_url = rtsp_url
        self.target_encodings = target_encodings  # List of known face encodings
        self.socketio = socketio
        self.target_fps = target_fps
        self.stream = None
        self.tracker = TemporalConsistencyTracker(required_consecutive=required_consecutive)
        self.running = False
        self.process_thread = None
        self.frame_skip = 1
    
    def start(self):
        """Start stream processing"""
        self.stream = RTSPStreamCapture(self.rtsp_url).start()
        
        # Calculate frame skip based on stream FPS
        stream_fps = self.stream.get_fps()
        self.frame_skip = max(1, int(stream_fps / self.target_fps))
        
        self.running = True
        self.process_thread = threading.Thread(target=self._process_stream, daemon=True)
        self.process_thread.start()
        
        return self
    
    def _process_stream(self):
        """Main processing loop with frame skipping"""
        frame_count = 0
        
        while self.running:
            frame = self.stream.read()
            if frame is None:
                time.sleep(0.01)
                continue
            
            frame_count += 1
            
            # Dynamic frame skipping
            if frame_count % self.frame_skip != 0:
                continue
            
            # Process frame
            self._process_frame(frame, frame_count)
    
    def _process_frame(self, frame, frame_number):
        """Process single frame for face matching"""
        try:
            # Resize for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            face_locations = face_recognition.face_locations(rgb_frame, model='hog')
            if not face_locations:
                return
            
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            timestamp = time.time()
            
            # Match against target encodings
            for face_encoding, face_location in zip(face_encodings, face_locations):
                matches = face_recognition.compare_faces(
                    self.target_encodings, face_encoding, tolerance=0.6
                )
                face_distances = face_recognition.face_distance(
                    self.target_encodings, face_encoding
                )
                
                if True in matches:
                    best_match_idx = np.argmin(face_distances)
                    confidence = 1 - face_distances[best_match_idx]
                    
                    # Add to temporal tracker
                    is_verified, conf = self.tracker.add_detection(
                        best_match_idx, confidence, timestamp
                    )
                    
                    # Emit verified match via SocketIO
                    if is_verified and self.socketio:
                        self._emit_match(best_match_idx, conf, face_location, frame_number)
        
        except Exception as e:
            print(f"Frame processing error: {e}")
    
    def _emit_match(self, person_id, confidence, location, frame_number):
        """Emit verified match to frontend via SocketIO"""
        if not self.socketio:
            return
        
        match_data = {
            'person_id': int(person_id),
            'confidence': float(confidence),
            'location': {
                'top': location[0] * 2,
                'right': location[1] * 2,
                'bottom': location[2] * 2,
                'left': location[3] * 2
            },
            'frame_number': frame_number,
            'timestamp': datetime.now().isoformat(),
            'status': 'verified'
        }
        
        self.socketio.emit('person_detected', match_data, namespace='/live_tracking')
        print(f"✓ Verified match: Person {person_id} (confidence: {confidence:.2f})")
    
    def stop(self):
        """Stop stream processing"""
        self.running = False
        if self.process_thread:
            self.process_thread.join(timeout=2)
        if self.stream:
            self.stream.stop()
        self.tracker.reset()
    
    def is_running(self):
        """Check if processor is running"""
        return self.running

# Global processor registry
_active_processors = {}

def start_live_tracking(stream_id, rtsp_url, target_encodings, socketio, 
                       target_fps=5, required_consecutive=3):
    """
    Start live tracking for a stream
    
    Args:
        stream_id: Unique identifier for this stream
        rtsp_url: RTSP stream URL
        target_encodings: List of face encodings to match
        socketio: Flask-SocketIO instance
        target_fps: Target processing FPS (default: 5)
        required_consecutive: Required consecutive detections (default: 3)
    
    Returns:
        LiveStreamProcessor instance
    """
    if stream_id in _active_processors:
        stop_live_tracking(stream_id)
    
    processor = LiveStreamProcessor(
        rtsp_url, target_encodings, socketio, 
        target_fps, required_consecutive
    )
    processor.start()
    _active_processors[stream_id] = processor
    
    return processor

def stop_live_tracking(stream_id):
    """Stop live tracking for a stream"""
    if stream_id in _active_processors:
        _active_processors[stream_id].stop()
        del _active_processors[stream_id]

def stop_all_tracking():
    """Stop all active tracking streams"""
    for stream_id in list(_active_processors.keys()):
        stop_live_tracking(stream_id)

def get_active_streams():
    """Get list of active stream IDs"""
    return list(_active_processors.keys())
