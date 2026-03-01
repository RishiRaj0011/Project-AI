"""
Frame Enhancement Pipeline for CCTV Footage
Optimizes low-light and low-contrast frames for face recognition
"""
import cv2
import numpy as np

def enhance_frame_for_ai(frame):
    """
    Enhance CCTV frame for face recognition using CLAHE and denoising
    
    Args:
        frame: Input frame (BGR or grayscale numpy array)
    
    Returns:
        Enhanced frame in RGB format ready for face_recognition library
    """
    # Convert to BGR if grayscale
    if len(frame.shape) == 2:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    
    # Convert to LAB color space for better CLAHE results
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Apply CLAHE to L channel (lightness)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l)
    
    # Merge channels back
    lab_enhanced = cv2.merge([l_enhanced, a, b])
    enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
    
    # Apply light Gaussian blur to reduce noise while preserving edges
    enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0.5)
    
    # Convert BGR to RGB for face_recognition library
    enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
    
    return enhanced_rgb

def enhance_frame_aggressive(frame):
    """
    Aggressive enhancement for extremely poor quality footage
    """
    if len(frame.shape) == 2:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    
    # Denoise first
    denoised = cv2.fastNlMeansDenoisingColored(frame, None, 10, 10, 7, 21)
    
    # LAB + CLAHE
    lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l)
    
    lab_enhanced = cv2.merge([l_enhanced, a, b])
    enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
    
    # Sharpen edges
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)
    enhanced = cv2.addWeighted(enhanced, 0.7, sharpened, 0.3, 0)
    
    # Light blur
    enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0.5)
    
    return cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)

def enhance_frame_fast(frame):
    """
    Fast enhancement for real-time processing
    """
    if len(frame.shape) == 2:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    
    # Simple gamma correction for brightness
    gamma = 1.2
    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype("uint8")
    enhanced = cv2.LUT(frame, table)
    
    # CLAHE on grayscale
    gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray_enhanced = clahe.apply(gray)
    
    # Merge back to color
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_BGR2HSV)
    enhanced[:, :, 2] = gray_enhanced
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_HSV2BGR)
    
    # Light blur
    enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0.5)
    
    return cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
