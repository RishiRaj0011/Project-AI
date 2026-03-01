"""
Liveness Detection Module - Anti-Spoofing for Photo Uploads
Detects fake photos (screen captures, printed photos) using multiple techniques
"""
import cv2
import numpy as np
import dlib
from scipy.spatial import distance as dist

# Eye Aspect Ratio calculation
def eye_aspect_ratio(eye):
    """Calculate Eye Aspect Ratio (EAR) for blink detection"""
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

def detect_moire_patterns(image):
    """
    Detect moiré patterns typical in screen photos
    Returns score: higher = more likely a screen photo
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    
    # Apply FFT to detect periodic patterns
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)
    magnitude = np.abs(fshift)
    
    # Analyze high-frequency components (moiré patterns)
    h, w = magnitude.shape
    center_h, center_w = h // 2, w // 2
    mask = np.ones((h, w), dtype=np.uint8)
    cv2.circle(mask, (center_w, center_h), 30, 0, -1)
    
    high_freq_energy = np.sum(magnitude * mask) / np.sum(magnitude)
    return high_freq_energy

def detect_screen_glare(image):
    """
    Detect screen glare and reflections
    Returns score: higher = more likely a screen photo
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    
    # Detect bright spots (glare)
    _, bright_mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
    bright_ratio = np.sum(bright_mask > 0) / (gray.shape[0] * gray.shape[1])
    
    # Detect sharp edges (screen bezels)
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
    
    return bright_ratio + edge_density * 0.5

def analyze_texture_quality(image):
    """
    Analyze image texture - real faces have natural texture variation
    Screen photos have uniform/pixelated texture
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    
    # Calculate local binary pattern variance
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    texture_variance = laplacian.var()
    
    # Real faces: high variance (50-200), Screen photos: low variance (<30)
    return texture_variance

def detect_liveness(image_path, predictor_path="shape_predictor_68_face_landmarks.dat"):
    """
    Main liveness detection function
    
    Args:
        image_path: Path to uploaded image
        predictor_path: Path to dlib facial landmark predictor
    
    Returns:
        bool: True if real human, False if spoof/fake
    """
    try:
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            return False
        
        # Initialize dlib detector
        detector = dlib.get_frontal_face_detector()
        
        # Try to load predictor, fallback to basic checks if not available
        try:
            predictor = dlib.shape_predictor(predictor_path)
            use_landmarks = True
        except:
            use_landmarks = False
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = detector(gray, 1)
        
        if len(faces) == 0:
            return False  # No face detected
        
        # Score accumulator (higher = more likely real)
        liveness_score = 0
        
        # 1. Facial landmark analysis (if available)
        if use_landmarks:
            for face in faces:
                landmarks = predictor(gray, face)
                
                # Extract eye coordinates
                left_eye = [(landmarks.part(i).x, landmarks.part(i).y) for i in range(36, 42)]
                right_eye = [(landmarks.part(i).x, landmarks.part(i).y) for i in range(42, 48)]
                
                # Calculate EAR
                left_ear = eye_aspect_ratio(np.array(left_eye))
                right_ear = eye_aspect_ratio(np.array(right_eye))
                avg_ear = (left_ear + right_ear) / 2.0
                
                # Real faces: EAR typically 0.2-0.35
                # Screen photos: often abnormal EAR
                if 0.15 < avg_ear < 0.4:
                    liveness_score += 2
        else:
            # If no landmarks, give neutral score
            liveness_score += 1
        
        # 2. Moiré pattern detection
        moire_score = detect_moire_patterns(image)
        if moire_score < 0.15:  # Low moiré = likely real
            liveness_score += 2
        elif moire_score > 0.25:  # High moiré = likely fake
            liveness_score -= 2
        
        # 3. Screen glare detection
        glare_score = detect_screen_glare(image)
        if glare_score < 0.1:  # Low glare = likely real
            liveness_score += 2
        elif glare_score > 0.2:  # High glare = likely fake
            liveness_score -= 2
        
        # 4. Texture quality analysis
        texture_var = analyze_texture_quality(image)
        if texture_var > 50:  # High texture variance = real
            liveness_score += 2
        elif texture_var < 20:  # Low texture variance = fake
            liveness_score -= 2
        
        # 5. Color distribution analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        color_std = np.std(hsv[:, :, 1])  # Saturation std
        if color_std > 20:  # Natural color variation
            liveness_score += 1
        
        # Decision threshold
        return liveness_score >= 3
        
    except Exception as e:
        print(f"Liveness detection error: {e}")
        return False  # Fail-safe: reject on error

def detect_liveness_simple(image_path):
    """
    Simplified liveness detection without dlib landmarks
    Uses only image analysis techniques
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            return False
        
        # Basic face detection
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) == 0:
            return False
        
        score = 0
        
        # Moiré patterns
        if detect_moire_patterns(image) < 0.15:
            score += 2
        
        # Screen glare
        if detect_screen_glare(image) < 0.1:
            score += 2
        
        # Texture quality
        if analyze_texture_quality(image) > 50:
            score += 2
        
        # Color distribution
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        if np.std(hsv[:, :, 1]) > 20:
            score += 1
        
        return score >= 4
        
    except Exception as e:
        print(f"Simple liveness detection error: {e}")
        return False
