import cv2
import numpy as np
import math
import time
import argparse
import os
import json
import sqlite3
import hashlib
from datetime import datetime
import face_db_utils as db

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
        return hashlib.md5(str(time.time()).encode()).hexdigest()  # Fallback hash

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

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Face Detection with Conversational Interface')
    parser.add_argument('--camera', type=int, default=0, help='Camera index (0 for default/back, 1 for front if available)')
    parser.add_argument('--scale', type=float, default=1.3, help='Scale factor for face detection')
    parser.add_argument('--min-neighbors', type=int, default=5, help='Minimum neighbors for face detection')
    parser.add_argument('--mode', type=int, choices=[1, 2], help='1: Register new face, 2: Identify face')
    args = parser.parse_args()
    
    # Initialize the face detector
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    if face_cascade.empty():
        print("Error: Failed to load face cascade classifier")
        return
    
    # Initialize database
    db.create_db_tables()
    
    # If mode not specified, show menu
    if args.mode is None:
        show_menu()
        return
    
    # Start face detection based on mode
    if args.mode == 1:
        register_face(face_cascade, args)
    elif args.mode == 2:
        identify_face(face_cascade, args)
    else:
        show_menu()

def show_menu():
    """Display the main menu and process selection"""
    print("\n===== FACE DETECTION SYSTEM =====")
    print("1. Register a new face")
    print("2. Identify a face")
    print("0. Exit")
    print("================================")
    
    try:
        choice = input("Enter your choice (0-2): ")
        if choice == "1":
            os.system("python face_detection.py --mode 1")
        elif choice == "2":
            os.system("python face_detection.py --mode 2")
        elif choice == "0":
            print("Exiting program.")
            return
        else:
            print("Invalid choice. Please try again.")
            show_menu()
    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting.")
    except Exception as e:
        print(f"Error: {e}")
        show_menu()

def register_face(face_cascade, args):
    """Register a new face with a name"""
    print("\n===== REGISTERING NEW FACE =====")
    print("Please look at the camera and press 's' to start scanning.")
    print("Press 'q' to quit or return to menu.")
    
    # Start camera
    cap = setup_camera(args.camera)
    if not cap.isOpened():
        print(f"Error: Could not open camera {args.camera}")
        return
    
    # Get frame dimensions
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read from camera")
        cap.release()
        return
    
    height, width, _ = frame.shape
    
    # Setup parameters
    center_x, center_y = width // 2, height // 2
    max_radius = min(width, height) // 2 - 20
    min_radius = max_radius // 3
    
    # Animation parameters
    scan_radius = min_radius
    growing = True
    scan_complete = False
    scan_start_time = None
    face_detected = False
    detected_faces = []
    face_saved = False
    
    # UI colors
    circle_color = (0, 255, 0)  # Green
    scan_color = (0, 255, 255)  # Yellow
    text_color = (255, 255, 255)  # White
    face_color = (0, 0, 255)  # Red
    success_color = (0, 255, 0)  # Green
    
    # Main loop
    while True:
        # Capture frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame")
            break
        
        # Mirror the frame for a more natural selfie view
        frame = cv2.flip(frame, 1)
        
        # Create overlay for drawing
        overlay = frame.copy()
        output = frame.copy()
        
        # Draw guide circle
        cv2.circle(overlay, (center_x, center_y), max_radius, circle_color, 2)
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces with modified parameters for better face capture
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,  # More gradual scaling for better detection
            minNeighbors=5,
            minSize=(60, 80),  # Increase minimum face size, with more height
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Check if there's a face within the scanning circle
        face_in_circle = False
        current_faces = []
        
        for (x, y, w, h) in faces:
            # Increase the height of the face box by 15% to capture more of the face
            y_offset = int(h * 0.15)
            y = max(0, y - y_offset)
            h = min(frame.shape[0] - y, h + y_offset * 2)
            
            # Calculate face center
            face_center_x = x + w // 2
            face_center_y = y + h // 2
            
            # Calculate face distance from circle center
            distance = math.sqrt((face_center_x - center_x)**2 + (face_center_y - center_y)**2)
            
            # Calculate face radius (approximated by average of width and height)
            face_radius = (w + h) // 4
            
            # Extract face image for saving
            face_img = frame[y:y+h, x:x+w].copy()
            
            # Store face info
            current_faces.append({
                'x': x, 'y': y, 'w': w, 'h': h,
                'center': (face_center_x, face_center_y),
                'distance': distance,
                'radius': face_radius,
                'image': face_img,
                'timestamp': datetime.now().isoformat()
            })
            
            # Check if face is within the scanning circle
            if distance + face_radius <= scan_radius:
                face_in_circle = True
        
        # Draw scanning circle if scan is active
        if scan_start_time is not None and not scan_complete:
            if growing:
                scan_radius += 2  # scan animation speed
                if scan_radius >= max_radius:
                    growing = False
            else:
                scan_radius -= 2  # scan animation speed
                if scan_radius <= min_radius:
                    growing = True
            
            # Draw scanning circle
            cv2.circle(overlay, (center_x, center_y), scan_radius, scan_color, 2)
            
            # Draw scanning effect (pulse)
            alpha = 0.3
            pulse_radius = scan_radius + int(10 * math.sin(time.time() * 10))
            cv2.circle(overlay, (center_x, center_y), pulse_radius, scan_color, 1)
            
            # Check if face is detected during scan
            if face_in_circle:
                face_detected = True
                detected_faces = current_faces
                scan_complete = True
        
        # Draw detected faces
        for face in (detected_faces if scan_complete else current_faces):
            x, y, w, h = face['x'], face['y'], face['w'], face['h']
            
            # Draw face rectangle
            color = success_color if scan_complete and face_detected else face_color
            cv2.rectangle(overlay, (x, y), (x + w, y + h), color, 2)
            
            # Draw face center
            cv2.circle(overlay, face['center'], 2, color, -1)
            
            # Draw distance line from face to center if not scanned
            if not scan_complete:
                cv2.line(overlay, (center_x, center_y), face['center'], face_color, 1)
        
        # Blend overlay with original frame
        cv2.addWeighted(overlay, 0.7, output, 0.3, 0, output)
        
        # Add status text
        if scan_complete:
            if face_detected:
                cv2.putText(output, "Face Scan Complete!", (10, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, success_color, 2)
                
                if not face_saved:
                    cv2.putText(output, "Press SPACE to enter name", (10, 60),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, success_color, 2)
                else:
                    cv2.putText(output, "Face saved to database", (10, 60),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, success_color, 2)
            else:
                cv2.putText(output, "No face detected in scan area", (10, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, face_color, 2)
        elif scan_start_time is not None:
            cv2.putText(output, "Scanning...", (10, 30),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, scan_color, 2)
        else:
            cv2.putText(output, "Press 's' to start face scan", (10, 30),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)
        
        # Add instructions
        instruction_text = "Press 'q' to quit, 'r' to reset"
        cv2.putText(output, instruction_text, (10, height - 20),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)
        
        # Display output
        cv2.imshow("Face Registration", output)
        
        # Check for key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s') and scan_start_time is None:
            # Start scanning
            scan_start_time = time.time()
            scan_radius = min_radius
            growing = True
            scan_complete = False
            face_detected = False
            detected_faces = []
            face_saved = False
        elif key == ord('r'):
            # Reset scan
            scan_start_time = None
            scan_complete = False
            face_detected = False
            detected_faces = []
            face_saved = False
        elif key == ord(' '):
            # Save face with name
            if scan_complete and face_detected and not face_saved:
                # Close window temporarily to get input
                cv2.destroyAllWindows()
                
                # Ask for name
                print("\nEnter the name for this face: ", end="")
                person_name = input().strip()
                
                if person_name:
                    for face in detected_faces:
                        saved_path = db.save_face_to_memory(face.copy(), person_name)
                        face_saved = True
                        print(f"\nFace saved and identified as: {person_name}")
                        print(f"Image saved to: {saved_path}")
                else:
                    print("\nNo name entered. Face not saved.")
                
                # Reopen window
                cv2.namedWindow("Face Registration")
                
                # If saved, return to menu after a delay
                if face_saved:
                    print("\nReturning to menu in 3 seconds...")
                    time.sleep(3)
                    break
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()
    print("Face registration completed")
    
    # Return to menu
    show_menu()

def identify_face(face_cascade, args):
    """Identify a face and welcome the person"""
    print("\n===== IDENTIFYING FACE =====")
    print("Please look at the camera and press 's' to start scanning.")
    print("Press 'q' to quit or return to menu.")
    
    # Start camera
    cap = setup_camera(args.camera)
    if not cap.isOpened():
        print(f"Error: Could not open camera {args.camera}")
        return
    
    # Get frame dimensions
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read from camera")
        cap.release()
        return
    
    height, width, _ = frame.shape
    
    # Setup parameters
    center_x, center_y = width // 2, height // 2
    max_radius = min(width, height) // 2 - 20
    min_radius = max_radius // 3
    
    # Animation parameters
    scan_radius = min_radius
    growing = True
    scan_complete = False
    scan_start_time = None
    face_detected = False
    detected_faces = []
    face_identified = False
    identified_person = None
    comparison_in_progress = False
    
    # UI colors
    circle_color = (0, 255, 0)  # Green
    scan_color = (0, 255, 255)  # Yellow
    text_color = (255, 255, 255)  # White
    face_color = (0, 0, 255)  # Red
    success_color = (0, 255, 0)  # Green
    
    # Main loop
    while True:
        # Capture frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame")
            break
        
        # Mirror the frame for a more natural selfie view
        frame = cv2.flip(frame, 1)
        
        # Create overlay for drawing
        overlay = frame.copy()
        output = frame.copy()
        
        # Draw guide circle
        cv2.circle(overlay, (center_x, center_y), max_radius, circle_color, 2)
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces with modified parameters for better face capture
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,  # More gradual scaling for better detection
            minNeighbors=5,
            minSize=(60, 80),  # Increase minimum face size, with more height
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Check if there's a face within the scanning circle
        face_in_circle = False
        current_faces = []
        
        for (x, y, w, h) in faces:
            # Increase the height of the face box by 15% to capture more of the face
            y_offset = int(h * 0.15)
            y = max(0, y - y_offset)
            h = min(frame.shape[0] - y, h + y_offset * 2)
            
            # Calculate face center
            face_center_x = x + w // 2
            face_center_y = y + h // 2
            
            # Calculate face distance from circle center
            distance = math.sqrt((face_center_x - center_x)**2 + (face_center_y - center_y)**2)
            
            # Calculate face radius (approximated by average of width and height)
            face_radius = (w + h) // 4
            
            # Extract face image for saving
            face_img = frame[y:y+h, x:x+w].copy()
            
            # Store face info
            current_faces.append({
                'x': x, 'y': y, 'w': w, 'h': h,
                'center': (face_center_x, face_center_y),
                'distance': distance,
                'radius': face_radius,
                'image': face_img,
                'timestamp': datetime.now().isoformat()
            })
            
            # Check if face is within the scanning circle
            if distance + face_radius <= scan_radius:
                face_in_circle = True
        
        # Draw scanning circle if scan is active
        if scan_start_time is not None and not scan_complete:
            if growing:
                scan_radius += 2  # scan animation speed
                if scan_radius >= max_radius:
                    growing = False
            else:
                scan_radius -= 2  # scan animation speed
                if scan_radius <= min_radius:
                    growing = True
            
            # Draw scanning circle
            cv2.circle(overlay, (center_x, center_y), scan_radius, scan_color, 2)
            
            # Draw scanning effect (pulse)
            alpha = 0.3
            pulse_radius = scan_radius + int(10 * math.sin(time.time() * 10))
            cv2.circle(overlay, (center_x, center_y), pulse_radius, scan_color, 1)
            
            # Check if face is detected during scan
            if face_in_circle:
                face_detected = True
                detected_faces = current_faces
                scan_complete = True
                
                # Try to identify the face in a non-blocking way
                if not face_identified and not comparison_in_progress and len(detected_faces) > 0:
                    comparison_in_progress = True
                    print("\nAttempting to identify face...")
                    
                    # Perform face matching
                    match_result = db.find_matching_face(detected_faces[0]['image'])
                    comparison_in_progress = False
                    
                    if match_result['exists']:
                        face_identified = True
                        identified_person = match_result
                        confidence = match_result.get('confidence', 1.0) * 100
                        print(f"\nFace identified as: {match_result['name']} (Confidence: {confidence:.1f}%)")
                        print(f"Welcome back, {match_result['name']}!")
                    else:
                        print("\nNo matching face found in database.")
        
        # Draw detected faces
        for face in (detected_faces if scan_complete else current_faces):
            x, y, w, h = face['x'], face['y'], face['w'], face['h']
            
            # Draw face rectangle
            color = success_color if scan_complete and face_detected else face_color
            if face_identified:
                color = (0, 255, 0)  # Green for identified face
            
            cv2.rectangle(overlay, (x, y), (x + w, y + h), color, 2)
            
            # Draw face center
            cv2.circle(overlay, face['center'], 2, color, -1)
            
            # Draw distance line from face to center if not scanned
            if not scan_complete:
                cv2.line(overlay, (center_x, center_y), face['center'], face_color, 1)
        
        # Blend overlay with original frame
        cv2.addWeighted(overlay, 0.7, output, 0.3, 0, output)
        
        # Add status text
        if scan_complete:
            if face_detected:
                cv2.putText(output, "Face Scan Complete!", (10, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, success_color, 2)
                
                if face_identified:
                    # Display confidence if available
                    confidence_text = ""
                    if 'confidence' in identified_person:
                        confidence = identified_person['confidence'] * 100
                        confidence_text = f" ({confidence:.1f}%)"
                    
                    # Display name with confidence
                    cv2.putText(output, f"Welcome, {identified_person['name']}!{confidence_text}", (10, 60),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, success_color, 2)
                    
                    # Add ID info
                    cv2.putText(output, f"ID: {identified_person['id']}", (10, 90),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, success_color, 2)
                    
                elif comparison_in_progress:
                    cv2.putText(output, "Analyzing face...", (10, 60),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                else:
                    cv2.putText(output, "Face not recognized", (10, 60),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, face_color, 2)
                    cv2.putText(output, "Press 'r' to register this face", (10, 90),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)
            else:
                cv2.putText(output, "No face detected in scan area", (10, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, face_color, 2)
        elif scan_start_time is not None:
            cv2.putText(output, "Scanning...", (10, 30),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, scan_color, 2)
        else:
            cv2.putText(output, "Press 's' to start face scan", (10, 30),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)
        
        # Add instructions
        instruction_text = "Press 'q' to quit, 'r' to reset"
        cv2.putText(output, instruction_text, (10, height - 20),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)
        
        # Display output
        cv2.imshow("Face Identification", output)
        
        # Check for key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s') and scan_start_time is None:
            # Start scanning
            scan_start_time = time.time()
            scan_radius = min_radius
            growing = True
            scan_complete = False
            face_detected = False
            detected_faces = []
            face_identified = False
            identified_person = None
            comparison_in_progress = False
        elif key == ord('r'):
            # Reset scan or switch to registration if face not recognized
            if scan_complete and face_detected and not face_identified:
                cv2.destroyAllWindows()
                cap.release()
                print("\nSwitching to face registration...")
                register_face(face_cascade, args)
                return
            else:
                scan_start_time = None
                scan_complete = False
                face_detected = False
                detected_faces = []
                face_identified = False
                identified_person = None
                comparison_in_progress = False
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()
    print("Face identification completed")
    
    # Return to menu
    show_menu()

def setup_camera(camera_index):
    """Initialize and setup the camera"""
    cap = cv2.VideoCapture(camera_index)
    if cap.isOpened():
        # Set camera resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return cap

if __name__ == "__main__":
    main() 