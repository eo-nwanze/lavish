import cv2
import numpy as np
import json
import sys
import face_db_utils as db
from datetime import datetime
import time
import math
import os

def identify_face_from_camera():
    """Capture an image from camera and identify the face"""
    try:
        # Use the better implementation with full UI
        return process_face_directly("identify")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return json.dumps({"error": f"Error during face identification: {str(e)}"})

def process_face_directly(query=None, headless=None):
    """Process face-related commands directly without MCP initialization
    
    Args:
        query: Optional text query containing commands or the person's name
        headless: If True, run in headless mode without UI (for identification)
        
    Returns:
        A JSON string with the result of the operation
    """
    try:
        # Initialize basic variables
        operation = "identify"  # default operation
        person_name = None
        
        # Parse the query if provided
        if query:
            query_lower = query.lower()
            
            # Determine operation type
            if "register" in query_lower:
                operation = "register"
                # Force headless off for registration
                headless = False
                
                # Extract name from query if it's a registration
                if " as " in query_lower:
                    person_name = query_lower.split(" as ")[1].strip()
                elif "name is " in query_lower:
                    person_name = query_lower.split("name is ")[1].strip()
                elif "register " in query_lower and "face" in query_lower:
                    # Try to extract name after "register face"
                    parts = query_lower.split("register face")
                    if len(parts) > 1:
                        name_part = parts[1].strip()
                        # Remove common prefixes
                        for prefix in ["for ", "of ", "as "]:
                            if name_part.startswith(prefix):
                                person_name = name_part[len(prefix):]
                                break
                        if not person_name:
                            person_name = name_part

        # For identification, default to headless mode
        if operation == "identify" and headless is None:
            headless = True
            
        # Make sure we have a name for registration
        if operation == "register" and not person_name:
            # Prompt for name if not provided
            print("\nPlease enter a name for this face registration:")
            person_name = input().strip()
            if not person_name:
                return json.dumps({
                    "operation": "register",
                    "success": False,
                    "message": "Registration cancelled. Name is required."
                })
                
        # Print operation banner
        print("\n" + "="*50)
        print(f"STARTING {'REGISTRATION' if operation == 'register' else 'IDENTIFICATION'} PROCESS")
        print("="*50)
        
        # Initialize terminal progress
        progress_stages = ["Initializing Camera", "Detecting Face", "Processing", "Completing"]
        current_stage = 0
        
        # Display initial progress
        _display_progress_bar(current_stage, len(progress_stages), progress_stages[current_stage])
        
        # Initialize camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return json.dumps({"error": "Could not open camera."})
            
        # Get frame dimensions for UI
        ret, frame = cap.read()
        if not ret:
            cap.release()
            return json.dumps({"error": "Could not read from camera."})
        
        # Update progress
        current_stage = 1
        _display_progress_bar(current_stage, len(progress_stages), progress_stages[current_stage])
            
        height, width, _ = frame.shape
        
        # Setup parameters for face scanning UI
        center_x, center_y = width // 2, height // 2
        max_radius = min(width, height) // 2 - 20
        min_radius = max_radius // 3
        
        # Animation parameters
        scan_radius = min_radius
        growing = True
        scan_complete = False
        scan_start_time = time.time()
        min_scan_time = 3.0 if headless else 5.0  # Shorter time for headless mode
        face_detected = False
        detected_faces = []
        face_saved = False
        face_identified = False
        identified_person = None
        
        # UI colors
        circle_color = (0, 255, 0)  # Green
        scan_color = (0, 255, 255)  # Yellow
        text_color = (255, 255, 255)  # White
        face_color = (0, 0, 255)  # Red
        success_color = (0, 255, 0)  # Green
            
        # Show preview mode info
        if operation == "register":
            print(f"\nRegistration mode active. Please position your face for {person_name or 'Unknown'}")
            title = "Face Registration"
        else:
            print("\nIdentification mode active. Please look at the camera.")
            if not headless:
                title = "Face Identification"
            
        # Initialize face detector
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        if face_cascade.empty():
            return json.dumps({"error": "Failed to load face cascade classifier."})
        
        # Initialize profile face detector for side views
        profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
        
        # Timeout settings
        max_scan_time = 30.0 if headless else 60.0  # Shorter timeout for headless mode
        no_face_timeout = 15.0 if headless else 30.0  # Shorter timeout for headless mode
        last_face_time = time.time()  # Time when face was last detected
        
        # Instructions already displayed message
        instructions_shown = False
        
        # Detection progress percentage
        detection_progress = 0
        
        # For headless mode, show text indication
        if headless:
            print("\nRunning in headless mode (no preview window)")
            print("Please look directly at the camera...")
            
        # Main scanning loop with UI
        while True:
            # Check for timeout conditions
            current_time = time.time()
            elapsed_time = current_time - scan_start_time
            
            # Maximum time limit reached
            if elapsed_time > max_scan_time:
                print("\nMaximum scan time reached. Scan cancelled.")
                break
            
            # No face timeout check
            if not face_detected and current_time - last_face_time > no_face_timeout:
                print("\nNo face detected for too long. Scan cancelled.")
                break
            
            # Capture frame
            ret, frame = cap.read()
            if not ret:
                break
            
            # Mirror the frame for a more natural selfie view
            frame = cv2.flip(frame, 1)
            
            # Create a copy for processing (no drawing in headless mode)
            output = frame.copy()
            
            # Only create overlay and draw UI in non-headless mode
            if not headless:
                # Create overlay for drawing
                overlay = frame.copy()
                
                # Draw guide circle
                cv2.circle(overlay, (center_x, center_y), max_radius, circle_color, 2)
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply image enhancements for better face detection
            gray = _enhance_image_for_detection(gray)
            
            # Detect faces with modified parameters for better face capture
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,  # More gradual scaling for better detection
                minNeighbors=4,
                minSize=(60, 60),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            # If no faces found, try with profile face detection
            if len(faces) == 0:
                profile_faces = profile_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=3,
                    minSize=(60, 60),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                # If profile faces found, add them to our faces list
                if len(profile_faces) > 0:
                    faces = profile_faces
            
            # If still no faces found, try with more lenient parameters
            if len(faces) == 0:
                faces = face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.2,  # More lenient scale factor
                    minNeighbors=3,   # Fewer neighbors required
                    minSize=(30, 30), # Smaller minimum face size
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                # Try one more time with even more lenient params
                if len(faces) == 0:
                    faces = face_cascade.detectMultiScale(
                        gray,
                        scaleFactor=1.3,  # Even more lenient
                        minNeighbors=2,
                        minSize=(20, 20),
                        flags=cv2.CASCADE_SCALE_IMAGE
                    )
            
            # Check if there's a face within the scanning circle
            face_in_circle = False
            current_faces = []
            
            for (x, y, w, h) in faces:
                # Dynamic face box adjustment based on face size
                # Wider box for wider faces (based on aspect ratio)
                aspect_ratio = w / h
                
                # Add more width for wider faces
                if aspect_ratio > 0.8:  # Wider face
                    x_offset = int(w * 0.1)
                    x = max(0, x - x_offset)
                    w = min(frame.shape[1] - x, w + x_offset * 2)
                
                # Adjust height - increase top portion to include forehead
                y_offset_top = int(h * 0.2)    # More offset at top for forehead
                y_offset_bottom = int(h * 0.1)  # Less offset at bottom
                
                y = max(0, y - y_offset_top)
                h = min(frame.shape[0] - y, h + y_offset_top + y_offset_bottom)
                
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
                    'image': face_img
                })
                
                # Check if face is within the scanning circle
                if distance + face_radius <= scan_radius:
                    face_in_circle = True
                    
                # Update last face time
                last_face_time = current_time
            
            # Update scan radius animation (even in headless mode for internal logic)
            if growing:
                scan_radius += 2  # scan animation speed
                if scan_radius >= max_radius:
                    growing = False
            else:
                scan_radius -= 2  # scan animation speed
                if scan_radius <= min_radius:
                    growing = True
            
            # Draw UI elements only in non-headless mode
            if not headless:
                # Draw scanning circle
                cv2.circle(overlay, (center_x, center_y), scan_radius, scan_color, 2)
                
                # Draw scanning effect (pulse)
                pulse_radius = scan_radius + int(10 * math.sin(time.time() * 10))
                cv2.circle(overlay, (center_x, center_y), pulse_radius, scan_color, 1)
            
            # Update detection progress percentage for progress bar
            if current_faces:
                # If faces detected, calculate progress based on time and position
                best_face = min(current_faces, key=lambda f: f['distance']) if current_faces else None
                if best_face:
                    # Progress based on face position and elapsed time
                    distance_factor = max(0, 1 - (best_face['distance'] / max_radius))
                    time_factor = min(1, elapsed_time / min_scan_time)
                    detection_progress = int((distance_factor * 0.7 + time_factor * 0.3) * 100)
                    
                    # Update terminal progress bar with detection percentage
                    _display_progress_bar(current_stage, len(progress_stages), 
                                         f"{progress_stages[current_stage]} - Face detected ({detection_progress}%)")
            else:
                # If no faces, progress is just based on elapsed time
                detection_progress = int((elapsed_time / min_scan_time) * 30)  # Max 30% without face
                _display_progress_bar(current_stage, len(progress_stages), 
                                     f"{progress_stages[current_stage]} - Searching for face...")
            
            # Check if scan time is sufficient and face is detected to complete scan
            if face_in_circle and elapsed_time >= min_scan_time and not scan_complete:
                face_detected = True
                detected_faces = current_faces
                scan_complete = True
                print("\nFace scan complete! Face detected.")
                
                # Update progress to next stage
                current_stage = 2
                _display_progress_bar(current_stage, len(progress_stages), progress_stages[current_stage])
            
            # Only draw face boxes and UI in non-headless mode
            if not headless:
                # Draw detected faces
                for face in (detected_faces if scan_complete else current_faces):
                    x, y, w, h = face['x'], face['y'], face['w'], face['h']
                    
                    # Draw face rectangle
                    color = success_color if scan_complete and face_detected else face_color
                    cv2.rectangle(overlay, (x, y), (x + w, y + h), color, 2)
                    
                    # Draw face center
                    cv2.circle(overlay, face['center'], 2, color, -1)
                    
                    # Add guide lines to help positioning
                    if not scan_complete:
                        # Draw lines to center
                        cv2.line(overlay, (center_x, center_y), face['center'], face_color, 1)
                        
                        # Draw horizontal and vertical alignment guides
                        cv2.line(overlay, (face['center'][0], 0), (face['center'][0], height), (100, 100, 255), 1)
                        cv2.line(overlay, (0, face['center'][1]), (width, face['center'][1]), (100, 100, 255), 1)
                
                # Blend overlay with original frame
                cv2.addWeighted(overlay, 0.7, output, 0.3, 0, output)
                
                # Add status text
                if scan_complete:
                    if face_detected:
                        cv2.putText(output, "Face Scan Complete!", (10, 30),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, success_color, 2)
                        
                        if operation == "register":
                            if not face_saved:
                                cv2.putText(output, "Press SPACE to save this face", (10, 60),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, success_color, 2)
                                cv2.putText(output, "Press 'r' to retake scan", (10, 90),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)
                            else:
                                cv2.putText(output, "Face saved successfully!", (10, 60),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, success_color, 2)
                        else:  # Identification mode
                            if face_identified:
                                # Display confidence
                                confidence = identified_person.get('confidence', 1.0) * 100
                                cv2.putText(output, f"Hello, {identified_person['name']}!", (10, 60),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, success_color, 2)
                                cv2.putText(output, f"Confidence: {confidence:.1f}%", (10, 90),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, success_color, 2)
                            else:
                                cv2.putText(output, "Face not recognized", (10, 60),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, face_color, 2)
                                cv2.putText(output, "Press 'r' to register this face", (10, 90),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)
                    else:
                        cv2.putText(output, "No face detected in scan area", (10, 30),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, face_color, 2)
                else:
                    cv2.putText(output, "Scanning for face...", (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, scan_color, 2)
                    # Display time remaining for minimum scan
                    remaining = max(0, min_scan_time - elapsed_time)
                    if remaining > 0:
                        cv2.putText(output, f"Keep still: {remaining:.1f}s", (10, 60),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, scan_color, 2)
                
                # Add instructions
                instruction_text = "Press 'q' to quit, 'r' to reset/retake scan, SPACE to capture"
                cv2.putText(output, instruction_text, (10, height - 20),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)
                
                # Add face position guidance if face detected but not centered
                if current_faces and not scan_complete:
                    best_face = min(current_faces, key=lambda f: f['distance'])
                    dx = best_face['center'][0] - center_x
                    dy = best_face['center'][1] - center_y
                    
                    direction = []
                    if abs(dx) > 20:
                        direction.append("right" if dx < 0 else "left")
                    if abs(dy) > 20:
                        direction.append("down" if dy < 0 else "up")
                    
                    if direction:
                        move_text = f"Move {' and '.join(direction)} to center"
                        cv2.putText(output, move_text, (center_x - 120, center_y + 150),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                
                # Draw face alignment grid
                _draw_alignment_grid(output, center_x, center_y, max_radius)
                
                # Add progress bar at the bottom of the screen
                progress_width = int((detection_progress / 100) * (width - 40))
                cv2.rectangle(output, (20, height - 50), (width - 20, height - 40), (50, 50, 50), -1)
                cv2.rectangle(output, (20, height - 50), (20 + progress_width, height - 40), scan_color, -1)
                
                # Add progress percentage text
                cv2.putText(output, f"{detection_progress}%", (width - 70, height - 55),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
            
            # Display keyboard instructions if not shown (even in headless mode)
            if not instructions_shown:
                # Show instructions on console
                if not headless:
                    print("\nScanning for face...")
                    print("- Press SPACE to accept a detected face")
                    print("- Press 'r' to reset the scan")
                    print("- Press 'q' to quit the scan")
                else:
                    print("\nScanning for face (headless mode)...")
                    print("- Please look directly at the camera")
                    print("- Processing will complete automatically")
                    
                instructions_shown = True
            
            # Display output (only in non-headless mode)
            if not headless:
                cv2.imshow(title, output)
            
            # Handle key presses (even in headless mode, but only check for quit)
            if headless:
                # In headless mode, just check for Ctrl+C or window close
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\nScan cancelled by user.")
                    break
            else:
                # Full key handling in non-headless mode
                key = cv2.waitKey(1) & 0xFF
                
                # Check for registration completion
                if scan_complete and face_detected and operation == "register" and key == ord(' '):
                    # Update progress to next stage
                    current_stage = 3
                    _display_progress_bar(current_stage, len(progress_stages), progress_stages[current_stage])
                    
                    # Show the face preview in a separate window for confirmation
                    if len(detected_faces) > 0:
                        # Find the best face (closest to center)
                        best_face = min(detected_faces, key=lambda f: f['distance'])
                        face_preview = best_face['image'].copy()
                        
                        # Enhance the preview image 
                        face_preview = _enhance_face_for_preview(face_preview)
                        
                        # Create preview window
                        cv2.imshow("Face Preview - Press SPACE to confirm, ESC to retake", cv2.resize(face_preview, (300, 300)))
                        
                        # Wait for confirmation
                        while True:
                            preview_key = cv2.waitKey(0) & 0xFF
                            if preview_key == ord(' '):  # Confirm
                                # Close preview window
                                cv2.destroyWindow("Face Preview - Press SPACE to confirm, ESC to retake")
                                
                                # Save face to database
                                face_data = best_face.copy()
                                
                                # Compute face hash for duplication detection
                                face_data['face_hash'] = db.compute_face_hash(face_data['image'])
                                
                                # Save face
                                image_path = db.save_face_to_memory(face_data, person_name)
                                
                                face_saved = True
                                
                                # Show success message
                                success_img = np.zeros((100, 400, 3), np.uint8)
                                cv2.putText(success_img, "Face Saved Successfully!", (50, 50),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                                cv2.imshow("Success", success_img)
                                cv2.waitKey(1500)
                                cv2.destroyWindow("Success")
                                
                                print(f"\nFace saved successfully as {person_name}!")
                                print(f"Image path: {image_path}")
                                
                                # Break out of inner loop
                                break
                                
                            elif preview_key == 27:  # ESC to retake
                                # Close preview window
                                cv2.destroyWindow("Face Preview - Press SPACE to confirm, ESC to retake")
                                
                                # Reset scan
                                scan_start_time = time.time()
                                scan_radius = min_radius
                                growing = True
                                scan_complete = False
                                face_detected = False
                                detected_faces = []
                                face_saved = False
                                
                                # Reset to detection stage
                                current_stage = 1
                                _display_progress_bar(current_stage, len(progress_stages), progress_stages[current_stage])
                                
                                print("\nRetaking face scan...")
                                
                                # Break out of inner loop
                                break
                
                # Manual commands available in non-headless mode
                if key == ord('q'):
                    print("\nScan cancelled by user.")
                    break
                elif key == ord('r'):
                    # Reset scan
                    scan_start_time = time.time()
                    scan_radius = min_radius
                    growing = True
                    scan_complete = False
                    face_detected = False
                    detected_faces = []
                    face_saved = False
                    face_identified = False
                    identified_person = None
                    
                    # Reset to detection stage
                    current_stage = 1
                    _display_progress_bar(current_stage, len(progress_stages), progress_stages[current_stage])
                    
                    print("\nScan reset. Starting new scan...")
                elif key == ord(' ') and not scan_complete and len(current_faces) > 0:
                    # Manual face capture when space is pressed
                    face_detected = True
                    detected_faces = current_faces
                    scan_complete = True
                    
                    # Update progress to next stage
                    current_stage = 2
                    _display_progress_bar(current_stage, len(progress_stages), progress_stages[current_stage])
                    
                    print("\nFace manually captured.")
            
            # Process identification if face was detected
            if scan_complete and face_detected and operation == "identify" and not face_identified:
                # Try to identify the face
                if len(detected_faces) > 0:
                    # Update progress to next stage
                    current_stage = 3
                    _display_progress_bar(current_stage, len(progress_stages), "Processing face recognition...")
                    
                    # Show processing message only in non-headless mode
                    if not headless:
                        processing_img = np.zeros((100, 400, 3), np.uint8)
                        cv2.putText(processing_img, "Processing...", (150, 50),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                        cv2.imshow("Processing", processing_img)
                        cv2.waitKey(1)
                    
                    # Find matching face
                    best_face = min(detected_faces, key=lambda f: f['distance'])
                    match_result = db.find_matching_face(best_face['image'])
                    
                    # Close processing window if not headless
                    if not headless and cv2.getWindowProperty("Processing", cv2.WND_PROP_VISIBLE) >= 1:
                        cv2.destroyWindow("Processing")
                    
                    if match_result['exists']:
                        face_identified = True
                        identified_person = match_result
                        
                        # Display matched image only in non-headless mode
                        if not headless and 'image_path' in match_result and os.path.exists(match_result['image_path']):
                            try:
                                matched_img = cv2.imread(match_result['image_path'])
                                if matched_img is not None:
                                    cv2.imshow("Matched Face", cv2.resize(matched_img, (200, 200)))
                            except Exception as e:
                                print(f"Error displaying matched face: {e}")
                        
                        # Print to console
                        confidence = identified_person.get('confidence', 1.0) * 100
                        print(f"\nFace identified as {identified_person['name']} with {confidence:.1f}% confidence.")
                    else:
                        print("\nFace detected but not recognized in database.")
                    
                    # For headless mode, exit loop immediately after identification attempt
                    if headless:
                        break
                    
                    # Wait after identification before exiting (non-headless only)
                    if not headless and face_identified:
                        # Start showing countdown
                        countdown_start = time.time()
                        countdown_time = 5.0  # Extended time to view result
                        
                        while time.time() - countdown_start < countdown_time:
                            # Update the countdown timer on the screen
                            countdown_frame = output.copy()
                            remaining = countdown_time - (time.time() - countdown_start)
                            cv2.putText(countdown_frame, f"Closing in {int(remaining)}...", (10, height - 50),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                            cv2.imshow(title, countdown_frame)
                            
                            # Check for early exit
                            if cv2.waitKey(100) != -1:
                                break
            
            # Check if we should auto-exit (non-headless mode)
            if not headless:
                auto_exit_condition = (operation == "register" and face_saved) or \
                                     (operation == "identify" and face_identified and \
                                      hasattr(locals(), 'countdown_start') and \
                                      time.time() - countdown_start >= countdown_time)
                if auto_exit_condition:
                    break
        
        # Final progress update
        _display_progress_bar(len(progress_stages)-1, len(progress_stages), "Completing")
        print("\nProcess completed.")
        
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        
        # Prepare result based on operation
        if operation == "register":
            if face_saved:
                return json.dumps({
                    "operation": "register",
                    "success": True,
                    "name": person_name,
                    "image_path": image_path,
                    "message": f"Face registered successfully as {person_name}!"
                })
            else:
                return json.dumps({
                    "operation": "register",
                    "success": False,
                    "message": "Face registration was cancelled or failed."
                })
        else:  # identify operation
            if face_identified:
                confidence = identified_person.get('confidence', 1.0) * 100
                return json.dumps({
                    "operation": "identify",
                    "identified": True,
                    "name": identified_person['name'],
                    "id": identified_person['id'],
                    "confidence": f"{confidence:.1f}%",
                    "confidence_value": confidence/100,
                    "image_path": identified_person.get('image_path', ''),
                    "message": f"Face identified as {identified_person['name']} with {confidence:.1f}% confidence."
                })
            elif face_detected:
                return json.dumps({
                    "operation": "identify",
                    "identified": False,
                    "message": "Face detected but not recognized in database."
                })
            else:
                return json.dumps({
                    "operation": "identify",
                    "identified": False,
                    "message": "No face detected. Please try again with better lighting or positioning."
                })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return json.dumps({
            "error": f"Error during face processing: {str(e)}",
            "operation": operation if 'operation' in locals() else "unknown"
        })

def _enhance_image_for_detection(image):
    """Apply image enhancements to improve face detection"""
    # Equalize histogram for better contrast
    enhanced = cv2.equalizeHist(image)
    
    # Apply slight Gaussian blur to reduce noise
    enhanced = cv2.GaussianBlur(enhanced, (5, 5), 0)
    
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(enhanced)
    
    return enhanced

def _enhance_face_for_preview(image):
    """Enhance face image for better preview and recognition"""
    # Convert to LAB color space
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    
    # Split the LAB image into L, A, and B channels
    l, a, b = cv2.split(lab)
    
    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_l = clahe.apply(l)
    
    # Merge the enhanced L channel with the original A and B channels
    enhanced_lab = cv2.merge((enhanced_l, a, b))
    
    # Convert back to BGR color space
    enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    
    # Slightly sharpen the image
    kernel = np.array([[-1, -1, -1],
                       [-1,  9, -1],
                       [-1, -1, -1]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)
    
    return sharpened

def _draw_alignment_grid(image, center_x, center_y, radius):
    """Draw face alignment grid to help with positioning"""
    # Draw center crosshair
    length = 10
    color = (150, 150, 150)
    
    # Horizontal line
    cv2.line(image, (center_x - length, center_y), (center_x + length, center_y), color, 1)
    # Vertical line
    cv2.line(image, (center_x, center_y - length), (center_x, center_y + length), color, 1)
    
    # Draw eye level guide (slightly above center)
    eye_level = center_y - int(radius * 0.15)
    cv2.line(image, (center_x - radius//2, eye_level), (center_x + radius//2, eye_level), color, 1)
    
    # Draw face width guides
    width_offset = int(radius * 0.6)
    cv2.line(image, (center_x - width_offset, center_y - radius//3), 
             (center_x - width_offset, center_y + radius//3), color, 1)
    cv2.line(image, (center_x + width_offset, center_y - radius//3), 
             (center_x + width_offset, center_y + radius//3), color, 1)

def _display_progress_bar(current, total, description="Processing"):
    """Display a terminal progress bar"""
    bar_length = 40
    filled_length = int(bar_length * current / total)
    
    # Create the progress bar
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    # Calculate percentage
    percent = int(100 * current / total)
    
    # Print the progress bar
    print(f"\r[{bar}] {percent}% | {description}", end='', flush=True)
    
    # Add newline if complete
    if current == total:
        print()

if __name__ == "__main__":
    # Check for arguments
    if len(sys.argv) > 1:
        # If arguments provided, process them
        result = process_face_directly(" ".join(sys.argv[1:]))
    else:
        # Otherwise run the default identification
        result = identify_face_from_camera()
    
    print(result) 