"""
Face Detection Adapter

This module acts as an adapter between the face_detection module that uses SQLite
and our Django models for face detection.
"""
import os
# import cv2
# import numpy as np
import hashlib
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from .models import FaceDetection, DetectionEvent, FacialIdentity

def compute_face_hash(face_img):
    """Generate a hash for face image to detect duplicates"""
    try:
        # Resize for consistent hash generation
        small_img = cv2.resize(face_img, (32, 32))
        # Convert to grayscale to focus on features not colors
        gray = cv2.cvtColor(small_img, cv2.COLOR_BGR2GRAY)
        # Create hash
        img_hash = hashlib.md5(gray.tobytes()).hexdigest()
        return img_hash
    except Exception as e:
        print(f"Error generating face hash: {e}")
        return hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()  # Fallback hash

def check_face_exists(face_hash):
    """Check if this face has been detected before using Django ORM"""
    try:
        face = FaceDetection.objects.filter(face_hash=face_hash).first()
        if face:
            return {
                'exists': True, 
                'id': face.id, 
                'name': face.name, 
                'image_path': face.image_path
            }
        else:
            return {'exists': False}
    except Exception as e:
        print(f"Error checking face existence: {e}")
        return {'exists': False}

@transaction.atomic
def save_to_database(face_data, person_name):
    """Save face data to Django database"""
    try:
        # Convert all numpy values to Python native types
        x = int(face_data.get('x', 0))
        y = int(face_data.get('y', 0))
        w = int(face_data.get('w', 0))
        h = int(face_data.get('h', 0))
        
        # Get other values, ensuring they're native Python types
        face_hash = face_data.get('face_hash', '')
        image_path = face_data.get('image_path', '')
        current_time = timezone.now()
        
        # Convert center coordinates to native Python integers
        center = face_data.get('center', (0, 0))
        if isinstance(center, tuple) and len(center) == 2:
            center = (int(center[0]), int(center[1]))
        
        # Convert other numeric values
        distance = float(face_data.get('distance', 0))
        radius = int(face_data.get('radius', 0))
        
        # Prepare metadata as a dict
        meta_data = {
            'center_x': center[0],
            'center_y': center[1],
            'distance': distance,
            'radius': radius
        }
        
        # Check if face exists
        face_exists = check_face_exists(face_hash)
        
        if face_exists['exists']:
            # Face already exists, update last detection
            face_id = face_exists['id']
            face = FaceDetection.objects.get(id=face_id)
            print(f"Face already exists in database as {face.name} (ID: {face_id})")
            
            # Update face entry if name has changed
            if person_name and person_name != face.name:
                face.name = person_name
                face.save(update_fields=['name'])
                print(f"Updated name from '{face.name}' to '{person_name}'")
            
            # Add new detection record
            DetectionEvent.objects.create(
                face=face,
                timestamp=current_time,
                detection_type="repeat_detection"
            )
        else:
            # New face, insert into database
            try:
                # Use placeholder if name is None
                name_to_save = person_name if person_name else "Unknown"
                
                # Insert new face record
                face = FaceDetection.objects.create(
                    name=name_to_save,
                    image_path=image_path,
                    timestamp=current_time,
                    face_hash=face_hash,
                    x=x,
                    y=y,
                    width=w,
                    height=h,
                    meta_data=meta_data
                )
                
                # Add detection record
                DetectionEvent.objects.create(
                    face=face,
                    timestamp=current_time,
                    detection_type="first_detection"
                )
                
                print(f"New face saved to database with ID: {face.id} and name: {name_to_save}")
                face_id = face.id
                
            except Exception as e:
                print(f"Database error: {e}")
                # Print the values for debugging
                print(f"Values: name={person_name}, path={image_path}, hash={face_hash}, x={x}, y={y}, w={w}, h={h}")
                raise
        
        return face_id
        
    except Exception as e:
        print(f"Error saving to database: {e}")
        import traceback
        traceback.print_exc()
        return None

def save_face_to_memory(face_data, person_name=None):
    """Save detected face information to Django database"""
    print(f"Attempting to save face data to Django database")
    
    # Create face detection folder if it doesn't exist
    face_folder = os.path.join(settings.MEDIA_ROOT, "detected_faces")
    if not os.path.exists(face_folder):
        os.makedirs(face_folder)
        print(f"Created directory: {face_folder}")
    
    # Generate a unique filename for this face capture
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    name_prefix = "unknown" if not person_name else person_name.lower().replace(" ", "_")
    face_filename = os.path.join(face_folder, f"{name_prefix}_{timestamp}.jpg")
    
    # Save a copy of the data before modifications
    processed_face_data = face_data.copy()
    
    # Compute face hash for duplication detection (before saving)
    if 'image' in processed_face_data:
        processed_face_data['face_hash'] = compute_face_hash(processed_face_data['image'])
    
    # Save the face image
    if 'image' in processed_face_data:
        try:
            # Save the image file to disk
            cv2.imwrite(face_filename, processed_face_data['image'])
            print(f"Saved face image to {face_filename}")
            
            # Update face data with the saved image path
            processed_face_data['image_path'] = face_filename
            
            # Save to Django database
            face_id = save_to_database(processed_face_data, person_name)
            if face_id:
                processed_face_data['id'] = face_id
                processed_face_data['name'] = person_name or "Unknown"
            
        except Exception as e:
            print(f"Error saving image: {e}")
            import traceback
            traceback.print_exc()
    
    return processed_face_data.get('id')

def link_facial_identity_to_user(user, face_id, face_name):
    """Link a facial identity to a user account for authentication"""
    try:
        # Get the face detection record
        face = FaceDetection.objects.get(id=face_id)
        
        # Create or update facial identity for user
        facial_identity, created = FacialIdentity.objects.update_or_create(
            user=user,
            defaults={
                'face_id': face_id,
                'face_name': face_name or user.username,
                'face_image_path': face.image_path,
                'enabled': True,
                'date_registered': timezone.now()
            }
        )
        
        # Update user's face_login_enabled setting
        user.face_login_enabled = True
        user.save(update_fields=['face_login_enabled'])
        
        return True, facial_identity
    except Exception as e:
        print(f"Error linking facial identity to user: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def get_all_faces():
    """Get all faces from Django database"""
    faces = FaceDetection.objects.all().order_by('-timestamp')
    return [(face.id, face.name or "Unknown", face.image_path, face.timestamp) for face in faces]

def get_face_details(face_id):
    """Get detailed information about a specific face from Django database"""
    try:
        face = FaceDetection.objects.get(id=face_id)
        
        # Get detection events
        detections = DetectionEvent.objects.filter(face=face).order_by('-timestamp')
        detection_events = [(det.timestamp, det.detection_type) for det in detections]
        
        return {
            'id': face.id,
            'name': face.name or "Unknown",
            'image_path': face.image_path,
            'timestamp': face.timestamp,
            'face_hash': face.face_hash,
            'x': face.x,
            'y': face.y,
            'width': face.width,
            'height': face.height,
            'meta_data': face.meta_data,
            'detections': detection_events
        }
    except FaceDetection.DoesNotExist:
        return None
    except Exception as e:
        print(f"Error retrieving face details: {e}")
        return None 