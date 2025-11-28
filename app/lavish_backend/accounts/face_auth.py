"""
Face authentication module for the accounts app.

This module handles the facial authentication process, including:
- Registering a user's face
- Authenticating a user via facial recognition
"""
import os
import json
import sys
import subprocess
import logging
import time
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import CustomUser, FacialIdentity

# Note: This module uses the face_detection package from the project root
# If you're getting import errors, make sure the face_detection directory 
# is in your Python path and the required dependencies are installed.
# You can install the dependencies with:
#   pip install -r face_detection/requirements.txt

# Configure logger
logger = logging.getLogger(__name__)

# Get the absolute path to the face_detection directory
FACE_DETECTION_DIR = os.path.join(settings.BASE_DIR, 'face_detection')

# Get the user model
User = get_user_model()

def run_face_detection(mode='identify', name=None, headless=True):
    """
    Run the face detection script with the specified mode.
    
    Args:
        mode (str): 'identify' or 'register'
        name (str): Name for registration (only needed for register mode)
        headless (bool): Whether to run in headless mode without UI
        
    Returns:
        dict: JSON response from face detection system
    """
    try:
        # Add face_detection directory to Python path
        if FACE_DETECTION_DIR not in sys.path:
            sys.path.append(FACE_DETECTION_DIR)
            
        # Show loading message in terminal
        if mode == 'register':
            print(f"⏳ Starting facial registration for {name}...")
        else:
            print("⏳ Starting facial identification scan...")
            
        # Try to import face_scan_tool directly
        try:
            import face_scan_tool
            
            # For registration, we need to provide a name
            if mode == 'register' and name:
                print("📸 Capturing face image. Please wait...")
                query = f"register face as {name}"
                result = face_scan_tool.process_face_directly(query, headless=headless)
                print("✅ Face capture completed")
            else:
                # For identification, just use default mode
                print("🔍 Scanning for facial match...")
                result = face_scan_tool.process_face_directly("identify", headless=headless)
                print("✅ Facial scan completed")
                
            # Parse JSON result
            return json.loads(result)
            
        except ImportError:
            logger.error("Could not import face_scan_tool module directly")
            print("⚠️ Using alternative face detection method...")
            
            # Fall back to subprocess method
            cmd = [
                sys.executable,
                os.path.join(FACE_DETECTION_DIR, 'face_scan_tool.py')
            ]
            
            if mode == 'register' and name:
                cmd.append(f"register face as {name}")
                print("📸 Capturing face image via subprocess. Please wait...")
            else:
                cmd.append("identify")
                print("🔍 Scanning for facial match via subprocess...")
                
            # Run the process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=FACE_DETECTION_DIR
            )
            
            stdout, stderr = process.communicate()
            
            if stderr:
                logger.error(f"Face detection stderr: {stderr.decode('utf-8')}")
                print(f"❌ Error in face detection: {stderr.decode('utf-8')[:100]}")
            else:
                print("✅ Face detection completed successfully")
                
            # Parse the JSON output
            return json.loads(stdout.decode('utf-8'))
            
    except Exception as e:
        logger.exception(f"Error running face detection: {str(e)}")
        print(f"❌ Face detection failed: {str(e)}")
        return {"error": str(e)}

def register_user_face(user, headless=False):
    """
    Register a user's face for facial authentication.
    
    Args:
        user: The user to register a face for
        headless: Whether to run in headless mode (without GUI)
    
    Returns:
        dict: A dictionary containing:
            - success: Whether the registration was successful
            - message: A message describing the result
            - image_path: The path to the saved face image (if successful)
    """
    try:
        print(f"🔹 Starting facial registration process for user: {user.username}")
        # Create the face_images directory if it doesn't exist
        face_dir = os.path.join(settings.MEDIA_ROOT, 'face_images')
        os.makedirs(face_dir, exist_ok=True)
        print(f"🔹 Created storage directory: {face_dir}")
        
        # Create a unique filename for the user's face image
        timestamp = int(time.time())
        face_image_path = f'face_images/face_{user.id}_{timestamp}.jpg'
        full_image_path = os.path.join(settings.MEDIA_ROOT, face_image_path)
        print(f"🔹 Face image will be saved to: {face_image_path}")
        
        if not CV2_AVAILABLE:
            return {
                'success': False,
                'message': 'OpenCV not available. Face registration is disabled.'
            }
            
        # Initialize the video capture
        print("🔹 Initializing camera...")
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            print("❌ Could not access camera")
            return {
                'success': False,
                'message': 'Could not access camera. Please make sure your camera is connected and not in use by another application.'
            }
        
        # Load face detection model from file
        print("🔹 Loading face detection model...")
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # For face registration, we need to be more cautious and take a clear face image
        # We'll only register a face if it's detected with confidence in multiple consecutive frames
        consecutive_detections = 0
        max_consecutive_needed = 5
        face_detected = False
        face_img = None
        
        if not headless:
            # Don't create OpenCV window - rely on browser-based camera interaction
            pass
            
        # Countdown before starting capture
        start_time = time.time()
        countdown_duration = 3  # seconds
        print(f"🔹 Starting {countdown_duration} second countdown...")
        
        while True:
            # Read a frame from the camera
            ret, frame = camera.read()
            if not ret:
                break
                
            # Calculate remaining countdown time
            elapsed_time = time.time() - start_time
            remaining_time = max(0, countdown_duration - elapsed_time)
            
            if remaining_time > 0:
                # Still in countdown mode
                if int(remaining_time) != int(remaining_time + 0.1):  # Only print when second changes
                    print(f"⏱️ Countdown: {int(remaining_time)}...")
                if not headless:
                    # Don't use cv2.imshow - we'll use the browser-based camera view
                    pass
                continue
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces in the frame
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            if len(faces) == 1:
                # A single face detected in the frame
                consecutive_detections += 1
                x, y, w, h = faces[0]
                
                # Draw rectangle around the detected face
                detection_frame = frame.copy()
                cv2.rectangle(detection_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Show progress
                progress_text = f"Hold still: {consecutive_detections}/{max_consecutive_needed}"
                cv2.putText(
                    detection_frame, 
                    progress_text, 
                    (30, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    1, 
                    (0, 255, 0), 
                    2
                )
                
                print(f"🔹 Face detected! Progress: {consecutive_detections}/{max_consecutive_needed}")
                
                if not headless:
                    # Don't use cv2.imshow - we'll use the browser-based camera view
                    pass
                
                # Check if we have enough consecutive detections
                if consecutive_detections >= max_consecutive_needed:
                    # We have a consistent face detection
                    face_detected = True
                    print("✅ Face successfully detected! Capturing image...")
                    
                    # Extract face region with some margin
                    margin = int(0.5 * w)  # 50% margin
                    face_img = frame[
                        max(0, y-margin):min(frame.shape[0], y+h+margin),
                        max(0, x-margin):min(frame.shape[1], x+w+margin)
                    ]
                    break
            else:
                # Reset consecutive detections if no face or multiple faces are detected
                consecutive_detections = 0
                
                if not headless:
                    # Show guidance message
                    if len(faces) == 0:
                        message = "No face detected. Please position your face in front of the camera."
                    else:
                        message = "Multiple faces detected. Please ensure only you are in the frame."
                    
                    guidance_frame = frame.copy()
                    cv2.putText(
                        guidance_frame, 
                        message, 
                        (30, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.7, 
                        (0, 0, 255), 
                        2
                    )
                    cv2.imshow('Face Registration', guidance_frame)
            
            # Check for quit command
            if not headless and cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Release camera and close windows
        camera.release()
        if not headless:
            # Don't try to destroy OpenCV windows - they shouldn't be created
            pass
        
        if not face_detected or face_img is None:
            return {
                'success': False,
                'message': 'Face registration failed. Could not detect a clear face in frame.'
            }
        
        # Save the face image
        cv2.imwrite(full_image_path, face_img)
        
        # Create or update the FacialIdentity record for the user
        try:
            facial_identity = FacialIdentity.objects.get(user=user)
            # Update existing record
            facial_identity.face_image_path = face_image_path
            facial_identity.date_registered = timezone.now()
            facial_identity.enabled = True
        except FacialIdentity.DoesNotExist:
            # Create new record
            facial_identity = FacialIdentity(
                user=user,
                face_id=int(time.time()),  # Use timestamp as temporary face_id
                face_image_path=face_image_path,
                face_name=user.username,
                enabled=True,
                date_registered=timezone.now()
            )
        
        # Save the facial identity record
        facial_identity.save()
        
        # Also update the user's face_login_enabled field
        user.face_login_enabled = True
        user.save(update_fields=['face_login_enabled'])
        
        return {
            'success': True,
            'message': 'Face registered successfully',
            'image_path': face_image_path
        }
        
    except Exception as e:
        logger.exception(f"Error during face registration: {str(e)}")
        return {
            'success': False,
            'message': f'Face registration error: {str(e)}'
        }

def authenticate_with_face(require_username=False, username=None, headless=False):
    """
    Authenticate a user using facial recognition.
    
    Args:
        require_username: Whether to require a username for authentication
        username: The username to authenticate (if require_username is True)
        headless: Whether to run in headless mode (without GUI)
    
    Returns:
        User or None: The authenticated user, or None if authentication failed
    """
    try:
        print("🔒 Starting facial authentication...")
        # Filter users who have facial authentication enabled
        facial_users = FacialIdentity.objects.filter(enabled=True)
        
        # If username is provided, filter to just that user
        if require_username and username:
            print(f"🔹 Authenticating specifically for user: {username}")
            facial_users = facial_users.filter(user__username=username)
        else:
            print(f"🔹 Performing facial authentication for any registered user")
        
        # If no users with facial authentication, return None
        if not facial_users.exists():
            print("❌ No users with facial authentication found")
            return None
        
        # Initialize the video capture
        print("🔹 Initializing camera...")
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            logger.error("Could not access camera for facial authentication")
            print("❌ Could not access camera")
            return None
        
        # Load face detection model
        print("🔹 Loading face detection model...")
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Set up face recognition comparison
        face_images = []
        face_users = []
        
        # Load all registered face images for comparison
        print(f"🔹 Loading {facial_users.count()} registered face images for comparison...")
        for facial_id in facial_users:
            user = facial_id.user
            full_path = os.path.join(settings.MEDIA_ROOT, facial_id.face_image_path)
            
            if os.path.exists(full_path):
                # Load the registered face image
                registered_img = cv2.imread(full_path)
                if registered_img is not None:
                    # Convert to grayscale
                    registered_gray = cv2.cvtColor(registered_img, cv2.COLOR_BGR2GRAY)
                    face_images.append(registered_gray)
                    face_users.append(user)
        
        if len(face_images) == 0:
            logger.error("No valid face images found for comparison")
            print("❌ No valid face images found in database")
            camera.release()
            return None
        
        # Setup for authentication
        auth_start_time = time.time()
        max_auth_time = 10  # seconds
        face_confidence_threshold = 0.6
        print(f"⏱️ Authentication timeout set to {max_auth_time} seconds")
        
        if not headless:
            # Don't create OpenCV window - rely on browser-based camera interaction
            pass
        
        print("📷 Scanning for face match...")
        while time.time() - auth_start_time < max_auth_time:
            ret, frame = camera.read()
            if not ret:
                break
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            # Draw remaining time
            remaining_time = max(0, max_auth_time - (time.time() - auth_start_time))
            if int(remaining_time) != int(remaining_time + 0.1):  # Only print when second changes
                print(f"⏱️ Time remaining: {int(remaining_time)} seconds")
            
            display_frame = frame.copy()
            cv2.putText(
                display_frame, 
                f"Time remaining: {int(remaining_time)}s", 
                (30, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, 
                (0, 255, 0), 
                2
            )
            
            if len(faces) == 1:
                # Single face detected
                print("🔹 Face detected, comparing with registered faces...")
                x, y, w, h = faces[0]
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Extract face region with margin
                margin = int(0.5 * w)
                face_roi = gray[
                    max(0, y-margin):min(gray.shape[0], y+h+margin),
                    max(0, x-margin):min(gray.shape[1], x+w+margin)
                ]
                
                # Resize for comparison if needed
                if face_roi.size > 0:
                    # Compare with registered faces
                    # Here we're using a simple approach for demo purposes
                    # For production, consider using a more sophisticated face recognition algorithm
                    best_match = None
                    best_score = 0
                    
                    for i, registered_face in enumerate(face_images):
                        # Resize to match for comparison
                        if face_roi.shape[0] > 0 and face_roi.shape[1] > 0 and registered_face.shape[0] > 0 and registered_face.shape[1] > 0:
                            # Resize to common size for comparison
                            common_size = (100, 100)
                            face_roi_resized = cv2.resize(face_roi, common_size)
                            registered_face_resized = cv2.resize(registered_face, common_size)
                            
                            # Calculate structural similarity
                            try:
                                # Using normalized cross-correlation as a simple similarity measure
                                # For a real system, use a more sophisticated algorithm
                                result = cv2.matchTemplate(face_roi_resized, registered_face_resized, cv2.TM_CCORR_NORMED)
                                similarity = result[0][0]
                                
                                if similarity > best_score:
                                    best_score = similarity
                                    best_match = face_users[i]
                            except Exception as e:
                                logger.error(f"Error comparing faces: {str(e)}")
                    
                    # Display confidence
                    cv2.putText(
                        display_frame, 
                        f"Confidence: {best_score:.2f}", 
                        (x, y-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.5, 
                        (0, 255, 0), 
                        1
                    )
                    print(f"🔹 Best match confidence: {best_score:.2f}")
                    
                    # Check if confidence meets threshold and we have a match
                    if best_score >= face_confidence_threshold and best_match is not None:
                        # Authentication successful
                        print(f"✅ Authentication successful for user: {best_match.username}")
                        camera.release()
                        if not headless:
                            cv2.destroyAllWindows()
                        
                        # Update last used timestamp
                        try:
                            facial_id = FacialIdentity.objects.get(user=best_match)
                            facial_id.last_used = timezone.now()
                            facial_id.save(update_fields=['last_used'])
                            print("✅ Updated last used timestamp")
                        except Exception as e:
                            logger.error(f"Error updating last used timestamp: {str(e)}")
                            print(f"⚠️ Could not update last used timestamp: {str(e)}")
                        
                        return best_match
                    else:
                        # Face detected but no match with sufficient confidence
                        print(f"⚠️ Face detected but confidence score {best_score:.2f} below threshold {face_confidence_threshold}")
                        cv2.putText(
                            display_frame, 
                            "No match", 
                            (x, y+h+20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            0.6, 
                            (0, 0, 255), 
                            2
                        )
            
            if not headless:
                # Don't use cv2.imshow - we'll use the browser-based camera view
                pass
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        # If we get here, authentication has failed (timeout or no match)
        print("❌ Facial authentication failed - no matching face found")
        
        # Cleanup
        camera.release()
        if not headless:
            # Don't try to destroy OpenCV windows - they shouldn't be created
            pass
            
        return None
            
    except Exception as e:
        logger.exception(f"Error during facial authentication: {str(e)}")
        print(f"❌ Error during facial authentication: {str(e)}")
        return None

def check_smile_detection():
    """
    Placeholder for smile detection feature.
    This would be expanded to detect smiles for enhanced security.
    
    Returns:
        bool: True if smile detected
    """
    # This is a stub that would be expanded with actual smile detection
    # using either OpenCV or a more advanced face analysis system
    return True 