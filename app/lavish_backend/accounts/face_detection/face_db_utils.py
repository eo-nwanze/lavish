import sqlite3
import json
import hashlib
import cv2
import numpy as np
from datetime import datetime
import os

def create_db_tables():
    """Create SQLite database tables if they don't exist"""
    conn = sqlite3.connect('detection.db')
    cursor = conn.cursor()
    
    # Create faces table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS faces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        image_path TEXT,
        timestamp TEXT,
        face_hash TEXT UNIQUE,
        x INTEGER,
        y INTEGER,
        width INTEGER,
        height INTEGER,
        meta_data TEXT
    )
    ''')
    
    # Create detections table to track each detection event
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS detections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        face_id INTEGER,
        timestamp TEXT,
        detection_type TEXT,
        FOREIGN KEY (face_id) REFERENCES faces(id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Database tables initialized")

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
    """Check if this face has been detected before"""
    conn = sqlite3.connect('detection.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, image_path FROM faces WHERE face_hash = ?", (face_hash,))
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        return {'exists': True, 'id': result[0], 'name': result[1], 'image_path': result[2]}
    else:
        return {'exists': False}

def save_to_database(face_data, person_name):
    """Save face data to SQLite database"""
    try:
        # Ensure tables exist
        create_db_tables()  
        
        # Convert all numpy values to Python native types
        x = int(face_data.get('x', 0))
        y = int(face_data.get('y', 0))
        w = int(face_data.get('w', 0))
        h = int(face_data.get('h', 0))
        
        # Get other values, ensuring they're native Python types
        face_hash = face_data.get('face_hash', '')
        image_path = face_data.get('image_path', '')
        timestamp = datetime.now().isoformat()
        
        # Convert center coordinates to native Python integers
        center = face_data.get('center', (0, 0))
        if isinstance(center, tuple) and len(center) == 2:
            center = (int(center[0]), int(center[1]))
        
        # Convert other numeric values
        distance = float(face_data.get('distance', 0))
        radius = int(face_data.get('radius', 0))
        
        # Prepare metadata as a simple dict with native Python types
        meta_data = {
            'center_x': center[0],
            'center_y': center[1],
            'distance': distance,
            'radius': radius
        }
        
        # Connect to database
        conn = sqlite3.connect('detection.db')
        cursor = conn.cursor()
        
        # Check if face exists
        face_exists = check_face_exists(face_hash)
        
        if face_exists['exists']:
            # Face already exists, update last detection
            face_id = face_exists['id']
            print(f"Face already exists in database as {face_exists['name']} (ID: {face_id})")
            
            # Update face entry if name has changed
            if person_name and person_name != face_exists['name']:
                cursor.execute(
                    "UPDATE faces SET name = ? WHERE id = ?", 
                    (person_name, face_id)
                )
                print(f"Updated name from '{face_exists['name']}' to '{person_name}'")
            
            # Add new detection record
            cursor.execute(
                "INSERT INTO detections (face_id, timestamp, detection_type) VALUES (?, ?, ?)",
                (face_id, timestamp, "repeat_detection")
            )
            conn.commit()
        else:
            # New face, insert into database
            try:
                # Use placeholder if name is None
                name_to_save = person_name if person_name else "Unknown"
                
                # Insert new face record
                cursor.execute(
                    "INSERT INTO faces (name, image_path, timestamp, face_hash, x, y, width, height, meta_data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        name_to_save,
                        image_path,
                        timestamp,
                        face_hash,
                        x,
                        y,
                        w,
                        h,
                        json.dumps(meta_data)
                    )
                )
                
                # Get the face ID of the inserted record
                face_id = cursor.lastrowid
                
                # Add detection record
                cursor.execute(
                    "INSERT INTO detections (face_id, timestamp, detection_type) VALUES (?, ?, ?)",
                    (face_id, timestamp, "first_detection")
                )
                
                conn.commit()
                print(f"New face saved to database with ID: {face_id} and name: {name_to_save}")
                
            except sqlite3.Error as e:
                print(f"SQLite error: {e}")
                # Print the values for debugging
                print(f"Values: name={person_name}, path={image_path}, hash={face_hash}, x={x}, y={y}, w={w}, h={h}")
                conn.rollback()
                face_id = None
        
        conn.close()
        return face_id
        
    except Exception as e:
        print(f"Error saving to database: {e}")
        import traceback
        traceback.print_exc()
        return None

def save_face_to_memory(face_data, person_name=None):
    """Save detected face information to memory.json and SQLite database"""
    memory_file = "memory.json"
    print(f"Attempting to save face data to memory.json")
    
    # Create face detection folder if it doesn't exist
    face_folder = "detected_faces"
    if not os.path.exists(face_folder):
        os.makedirs(face_folder)
        print(f"Created directory: {face_folder}")
    
    # Generate a unique filename for this face capture
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name_prefix = "unknown" if not person_name else person_name.lower().replace(" ", "_")
    face_filename = f"{face_folder}/{name_prefix}_{timestamp}.jpg"
    
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
            
            # Save to SQLite database first (before removing the image)
            # This ensures the database has all the data it needs
            face_id = save_to_database(processed_face_data, person_name)
            if face_id:
                processed_face_data['id'] = face_id
                processed_face_data['name'] = person_name or "Unknown"
            
            # Now remove the actual image data before saving to JSON
            # as JSON doesn't handle binary data well
            del processed_face_data['image']
            
        except Exception as e:
            print(f"Error saving image: {e}")
            import traceback
            traceback.print_exc()
    
    # Convert numpy types to python native types for JSON serialization
    for key in list(processed_face_data.keys()):  # Use list() to avoid modification during iteration
        if isinstance(processed_face_data[key], np.integer):
            processed_face_data[key] = int(processed_face_data[key])
        elif isinstance(processed_face_data[key], np.floating):
            processed_face_data[key] = float(processed_face_data[key])
        elif isinstance(processed_face_data[key], np.ndarray):
            processed_face_data[key] = processed_face_data[key].tolist()
        elif isinstance(processed_face_data[key], tuple) and any(isinstance(i, np.integer) for i in processed_face_data[key]):
            # Convert tuples containing numpy integers
            processed_face_data[key] = tuple(int(i) if isinstance(i, np.integer) else i for i in processed_face_data[key])
    
    # Always start with a clean structure
    memory_data = {
        "detected_faces": [],
        "last_updated": datetime.now().isoformat()
    }
    
    # Try to read existing data
    try:
        with open(memory_file, 'r') as file:
            content = file.read().strip()
            if content:
                try:
                    data = json.loads(content)
                    if isinstance(data, dict) and 'detected_faces' in data:
                        memory_data['detected_faces'] = data['detected_faces']
                except json.JSONDecodeError:
                    print("Invalid JSON in memory file, starting fresh")
    except Exception as e:
        print(f"Error reading memory file: {e}")
    
    # Add new face data
    memory_data['detected_faces'].append(processed_face_data)
    memory_data['last_updated'] = datetime.now().isoformat()
    
    # Write to file
    try:
        with open(memory_file, 'w') as file:
            json.dump(memory_data, file, indent=4)
        print(f"Successfully saved memory data with {len(memory_data['detected_faces'])} faces")
    except Exception as e:
        print(f"Error saving memory data: {e}")
        # Try to identify problematic keys
        try:
            # Test serialize each key individually
            problem_keys = []
            for key, value in processed_face_data.items():
                try:
                    json.dumps({key: value})
                except TypeError:
                    problem_keys.append(f"{key}: {type(value)}")
            if problem_keys:
                print(f"Problem keys: {', '.join(problem_keys)}")
        except Exception:
            pass
    
    return face_filename

def face_distance(face1, face2):
    """Calculate Mean Squared Error between two face images as a distance metric"""
    # Resize images to same dimensions for comparison
    face1_resized = cv2.resize(face1, (100, 100))
    face2_resized = cv2.resize(face2, (100, 100))
    
    # Convert to grayscale for more robust comparison
    face1_gray = cv2.cvtColor(face1_resized, cv2.COLOR_BGR2GRAY)
    face2_gray = cv2.cvtColor(face2_resized, cv2.COLOR_BGR2GRAY)
    
    # Equalize histograms for better lighting invariance
    face1_eq = cv2.equalizeHist(face1_gray)
    face2_eq = cv2.equalizeHist(face2_gray)
    
    # Calculate Mean Squared Error
    diff = cv2.absdiff(face1_eq, face2_eq)
    diff_square = cv2.multiply(diff, diff)
    mse = np.mean(diff_square)
    
    # Normalize score (lower is better match)
    return mse

def find_matching_face(face_img):
    """Find a matching face in the database using face similarity"""
    conn = sqlite3.connect('detection.db')
    cursor = conn.cursor()
    
    # Get all faces from database
    cursor.execute("SELECT id, name, image_path FROM faces")
    db_faces = cursor.fetchall()
    
    conn.close()
    
    if not db_faces:
        return {'exists': False, 'message': 'No faces in database'}
    
    best_match = None
    best_score = float('inf')  # Lower score is better (MSE)
    
    # Similarity threshold - LOWERED from 1000 to make matching more permissive
    similarity_threshold = 1200  # Higher threshold means more permissive matching
    
    # Extra strict threshold for potentially confusable names
    strict_threshold = 700  # For names that are similar (Emmanuel/Emily)
    
    for face_id, name, img_path in db_faces:
        if not os.path.exists(img_path):
            continue
            
        # Load the stored face image
        stored_face = cv2.imread(img_path)
        if stored_face is None:
            continue
            
        # Calculate similarity using MSE
        score = face_distance(face_img, stored_face)
        
        # Print comparison details for debugging
        print(f"Comparing with {name} (ID: {face_id}), Score: {score}")
        
        # Update best match if better score found
        if score < best_score:
            best_score = score
            best_match = (face_id, name, img_path, score)
    
    # If best match is below threshold, consider it a match
    if best_match and best_score < similarity_threshold:
        face_id, name, img_path, score = best_match
        # Calculate confidence (inverse of score, normalized)
        confidence = max(0, min(1.0, 1.0 - (best_score / similarity_threshold)))
        
        # Add extra check: For similar name patterns
        is_similar_name = False
        
        # Create a list of potentially confusable names
        confusable_pairs = [
            ("emmanuel", "emily"),
            ("michael", "michelle"),
            ("daniel", "danielle"),
            ("alex", "alexa"),
            ("robert", "roberta")
        ]
        
        # Check if the identified name is part of a confusable pair
        name_lower = name.lower()
        for name1, name2 in confusable_pairs:
            if name1 in name_lower or name2 in name_lower:
                is_similar_name = True
                break
        
        # For similar names, use a stricter threshold
        if is_similar_name and best_score > strict_threshold:
            print(f"Potential similar name confusion ({name_lower}). Score: {best_score} > {strict_threshold}")
            return {'exists': False, 'message': f'Face not recognized. Potential name confusion detected.'}
        
        return {
            'exists': True,
            'id': face_id,
            'name': name,
            'image_path': img_path,
            'confidence': confidence,
            'score': best_score
        }
    else:
        if best_match:
            return {'exists': False, 'message': f'No match found. Best candidate was {best_match[1]} with score {best_score}'}
        else:
            return {'exists': False, 'message': 'No potential matches found'}

def get_all_faces():
    """Get all faces from the database"""
    conn = sqlite3.connect('detection.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, image_path, timestamp FROM faces ORDER BY id DESC")
    faces = cursor.fetchall()
    
    conn.close()
    return faces

def get_face_details(face_id):
    """Get detailed information about a specific face"""
    conn = sqlite3.connect('detection.db')
    cursor = conn.cursor()
    
    # Get face info
    cursor.execute("""
        SELECT id, name, image_path, timestamp, face_hash, x, y, width, height, meta_data 
        FROM faces WHERE id = ?
    """, (face_id,))
    face = cursor.fetchone()
    
    if not face:
        conn.close()
        return None
    
    # Get detection history
    cursor.execute("""
        SELECT timestamp, detection_type FROM detections
        WHERE face_id = ? ORDER BY timestamp DESC
    """, (face_id,))
    detections = cursor.fetchall()
    
    conn.close()
    
    if face:
        try:
            meta_data = json.loads(face[9]) if face[9] else {}
        except:
            meta_data = {}
            
        return {
            'id': face[0],
            'name': face[1],
            'image_path': face[2],
            'timestamp': face[3],
            'face_hash': face[4],
            'x': face[5],
            'y': face[6],
            'width': face[7],
            'height': face[8],
            'meta_data': meta_data,
            'detections': detections
        }
    
    return None

def update_face_name(face_id, new_name):
    """Update the name of a face in the database"""
    conn = sqlite3.connect('detection.db')
    cursor = conn.cursor()
    
    # Get current name
    cursor.execute("SELECT name FROM faces WHERE id = ?", (face_id,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return False, "Face not found"
    
    old_name = result[0]
    
    # Update the name
    cursor.execute("UPDATE faces SET name = ? WHERE id = ?", (new_name, face_id))
    
    # Add an update event to detections
    cursor.execute(
        "INSERT INTO detections (face_id, timestamp, detection_type) VALUES (?, ?, ?)",
        (face_id, datetime.now().isoformat(), "name_updated")
    )
    
    conn.commit()
    conn.close()
    
    return True, f"Updated name from '{old_name}' to '{new_name}'"

def delete_face(face_id):
    """Delete a face from the database"""
    conn = sqlite3.connect('detection.db')
    cursor = conn.cursor()
    
    # Get image path to potentially delete the file
    cursor.execute("SELECT image_path FROM faces WHERE id = ?", (face_id,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return False, "Face not found"
    
    image_path = result[0]
    
    # Delete detections first (maintain referential integrity)
    cursor.execute("DELETE FROM detections WHERE face_id = ?", (face_id,))
    
    # Delete the face record
    cursor.execute("DELETE FROM faces WHERE id = ?", (face_id,))
    
    conn.commit()
    conn.close()
    
    # Optionally delete the image file
    try:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
            return True, f"Face ID {face_id} deleted with image file"
        else:
            return True, f"Face ID {face_id} deleted (image file not found)"
    except Exception as e:
        return True, f"Face ID {face_id} deleted from database but error removing image: {e}" 