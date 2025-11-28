try:
    from praisonaiagents import Agent, Agents, MCP
except ImportError:
    pass
import os
from dotenv import load_dotenv
import sys
try:
    import face_db_utils as db
except ImportError:
    pass
import json
from datetime import datetime
import time
import traceback
from typing import List, Dict
# Import BraveConnection only if it's available
try:
    from brave import BraveConnection
    brave_available = True
except ImportError:
    brave_available = False
    print("WARNING: 'brave' module not available. Brave search functionality will be disabled.")
from subprocess import run, PIPE
import cv2
import math
import numpy as np

# Load environment variables from env file
load_dotenv("env")  # Note: loading from "env" instead of ".env"

brave_api_key = os.getenv("BRAVE_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")

# Check if the API keys are available
if not brave_api_key:
    print("ERROR: BRAVE_API_KEY is not set in the environment variables.")
    print("Please make sure the 'env' file contains a valid BRAVE_API_KEY.")
    sys.exit(1)

if not groq_api_key:
    print("WARNING: GROQ_API_KEY is not set in the environment variables.")
    print("This may cause issues when using Groq models.")

print(f"BRAVE_API_KEY loaded successfully: {brave_api_key[:4]}{'*' * (len(brave_api_key) - 8)}{brave_api_key[-4:]}")
if groq_api_key:
    print(f"GROQ_API_KEY loaded successfully: {groq_api_key[:4]}{'*' * (len(groq_api_key) - 8)}{groq_api_key[-4:]}")

# Get the memory file path from environment
memory_file_path = os.getenv("MEMORY_FILE_PATH", "memory.json")

# Initialize database tables if they don't exist
db.create_db_tables()
print("Face recognition database initialized")

def get_recent_faces():
    """Get list of recent faces from database for AI context"""
    try:
        faces = db.get_all_faces()
        if not faces or len(faces) == 0:
            return "No faces in database."
        
        # Format face information
        result = "Recent faces in database:\n"
        for i, face in enumerate(faces[:5]):  # Only return the 5 most recent
            result += f"ID: {face[0]}, Name: {face[1]}, Image: {face[2]}, Time: {face[3]}\n"
        
        if len(faces) > 5:
            result += f"...and {len(faces) - 5} more faces."
        
        return result
    except Exception as e:
        return f"Error retrieving faces: {e}"

class FaceRecognitionSystem:
    """Main class to handle face recognition interactions"""
    
    def __init__(self):
        # Simplified initialization to avoid MCP timeout
        # Use direct function calls instead of agents when possible
        try:
            # Set direct mode to True to bypass MCP for face operations
            self.direct_mode = True
            
            # Load database context about existing faces immediately
            self.db_context = get_recent_faces()
            
            # Initialize memory agent with higher timeout and delayed loading
            print("Initializing memory agent (with extended timeout)...")
            
            # Check if we can create a valid agent object
            try:
                self.memory_agent = Agent(
                    instructions="""You are a helpful assistant that can store and retrieve information.""",
                    llm="groq/meta-llama/llama-4-scout-17b-16e-instruct",
                    # Longer timeout for MCP initialization
                    tools=MCP("npx -y @modelcontextprotocol/server-memory", 
                          env={"MEMORY_FILE_PATH": memory_file_path},
                          timeout=120)  # Increased timeout to 120 seconds
                )
                print("Memory agent initialized successfully")
            except Exception as e:
                print(f"Failed to initialize memory agent: {e}")
                self.memory_agent = None
            
            # Initialize other agents only when needed (lazy loading)
            self._face_detection_agent = None
            self._sql_agent = None
            
            # Use direct Python function calls for face scanning to avoid timeouts
            self.direct_face_scan = True
            
            print("Face Recognition System initialized in direct mode")
            
        except Exception as e:
            print(f"Error during initialization: {e}")
            import traceback
            traceback.print_exc()
            # Fall back to direct mode only
            self.direct_mode = True
            self.direct_face_scan = True
            self.db_context = get_recent_faces()
    
    @property
    def face_detection_agent(self):
        """Lazy-loaded face detection agent to avoid startup delays"""
        if self._face_detection_agent is None and not self.direct_mode:
            print("Initializing face detection agent on first use...")
            self._face_detection_agent = Agent(
                instructions="""You are a security professional that can detect and analyze faces.""",
                llm="groq/meta-llama/llama-4-scout-17b-16e-instruct",
                tools=MCP("python face_detection.py", timeout=120)  # Doubled timeout
            )
        return self._face_detection_agent
    
    @property
    def sql_agent(self):
        """Lazy-loaded SQL agent to avoid startup delays"""
        if self._sql_agent is None and not self.direct_mode:
            print("Initializing SQL agent on first use...")
            self._sql_agent = Agent(
                instructions="""You are a database administrator for facial recognition data.""",
                llm="groq/meta-llama/llama-4-scout-17b-16e-instruct",
                tools=MCP("python db_manager.py $COMMAND --id $ID --name \"$NAME\" --query \"$QUERY\" --limit $LIMIT", 
                      timeout=120)  # Doubled timeout
            )
        return self._sql_agent
    
    def process_message(self, message):
        """Process a user message and determine appropriate action"""
        
        # Direct face scan request
        if "scan face" in message.lower() or "who am i" in message.lower() or "identify me" in message.lower():
            print("Performing direct face scan...")
            try:
                # Always use direct function call with headless mode for identification
                import face_scan_tool
                result = face_scan_tool.process_face_directly("identify", headless=True)
                
                # Parse the JSON result
                data = json.loads(result)
                if "error" in data:
                    return f"Error: {data['error']}"
                elif data.get("identified", False):
                    return f"Welcome, {data['name']}! (Confidence: {data['confidence']})"
                else:
                    return "Face detected but not recognized. Would you like to register this face?"
            except Exception as e:
                print(f"Error in direct face scan: {str(e)}")
                traceback.print_exc()
                return f"Error scanning face: {str(e)}"
        
        # Check if it's a direct command to launch facial recognition
        if "register face" in message.lower() or "register a face" in message.lower():
            print("\n" + "="*50)
            print("STARTING INTERACTIVE FACE REGISTRATION")
            print("="*50)
            
            # Check if name is already provided in the message
            name = None
            if " as " in message.lower():
                name = message.lower().split(" as ")[1].strip()
            elif "name is " in message.lower():
                name = message.lower().split("name is ")[1].strip()
            
            # If no name provided, prompt for one
            if not name:
                print("\nPlease enter a name for this face registration:")
                name = input().strip()
                
            if not name:
                return "Registration cancelled. Name is required."
            
            # Show instructions
            print(f"\nRegistering face as '{name}'...")
            print("\nInstructions:")
            print("- You will see a camera preview to help position your face")
            print("- Position your face in the scanning circle")
            print("- When your face is detected, press SPACE to capture")
            print("- Review the face preview and press SPACE to save or ESC to retake")
            print("- Press 'q' to cancel registration at any time")
            
            input("\nPress Enter to start the camera...")
                
            try:
                import face_scan_tool
                # Use non-headless mode for registration to show interactive preview
                result = face_scan_tool.process_face_directly(f"register face as {name}", headless=False)
                data = json.loads(result)
                
                if data.get("success", False):
                    # Verify face was saved properly
                    image_path = data.get('image_path', '')
                    if image_path and os.path.exists(image_path):
                        print(f"\n✓ Face successfully registered as {name}")
                        print(f"✓ Image saved to: {image_path}")
                        return f"Successfully registered face as {data.get('name')}!"
                    else:
                        print("⚠ Warning: Face was registered but image file could not be verified")
                        return f"Face registered as {data.get('name')}, but please verify the image was saved correctly."
                else:
                    error_msg = data.get('message', 'Unknown error')
                    print(f"✗ Registration failed: {error_msg}")
                    return f"Failed to register face: {error_msg}"
            except Exception as e:
                print(f"Error in face registration: {str(e)}")
                traceback.print_exc()
                return "Failed to register face. Please try again."
        
        elif "identify face" in message.lower() or "identify a face" in message.lower() or "recognize face" in message.lower():
            print("Starting face identification mode...")
            try:
                import face_scan_tool
                # Use headless mode for identification
                result = face_scan_tool.process_face_directly("identify", headless=True)
                data = json.loads(result)
                if data.get("identified", False):
                    return f"Hello, {data.get('name')}! Identified with {data.get('confidence', '?')} confidence."
                else:
                    return data.get('message', "Face detected but not recognized.")
            except Exception as e:
                print(f"Error in direct face identification: {str(e)}")
                return "Failed to identify face. Please try again."
        
        elif "list faces" in message.lower() or "show faces" in message.lower():
            print("Listing all faces in database...")
            try:
                # Direct database query instead of using agent
                faces = db.get_all_faces()
                if not faces:
                    return "No faces found in database."
                
                result = "Faces in database:\n"
                for face in faces:
                    result += f"ID: {face[0]}, Name: {face[1]}, Image: {face[2]}, Time: {face[3]}\n"
                return result
            except Exception as e:
                print(f"Error listing faces: {str(e)}")
                if self._sql_agent:
                    try:
                        return self._sql_agent.run("list")
                    except:
                        pass
                return "Failed to list faces from database."
        
        elif "face menu" in message.lower() or "launch face system" in message.lower():
            print("Starting the face recognition system...")
            return "Face recognition system is ready. You can use commands like 'scan face', 'register face as [name]', or 'identify me'."
        
        # Otherwise try to use memory agent if available
        if self.memory_agent:
            try:
                # Fixed: Use the correct method signature for calling the agent
                return self.memory_agent.run(message)
            except Exception as e:
                print(f"Error using memory agent: {e}")
                return f"I couldn't process that request through my memory system. Please try a face-related command instead."
        else:
            return "Memory agent not available. Please use face recognition commands like 'scan face' or 'register face as [name]'."

# Initialize the face recognition system
face_system = FaceRecognitionSystem()

# Use a face-related command directly to demonstrate functionality
user_message = "scan face"  # Changed to use face scanning immediately

# Process the message
try:
    print("\nRunning face detection command: 'scan face'")
    print("==============================================")
    response = face_system.process_message(user_message)
    print(response)
    print("==============================================")
    print("\nYou can now try other commands like:")
    print("- 'register face as [your name]'")
    print("- 'identify me'")
    print("- 'list faces'")
except Exception as e:
    print(f"Error processing message: {e}")
    traceback.print_exc()
    print("Face recognition system is ready. You can use commands like 'scan face', 'register face as [name]', or 'identify me'.")

# Load API key from .env file
def load_env():
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    # Check if API key is set
    api_key = os.environ.get('BRAVE_API_KEY', '')
    if api_key:
        print(f"BRAVE_API_KEY loaded successfully: {api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}")
    else:
        print("Warning: BRAVE_API_KEY not found in environment variables or .env file.")

# Face recognition function
def handle_face_command(query: str):
    """Handle face-related commands using the face recognition system"""
    try:
        # Check for registration request
        if "register" in query.lower() and "face" in query.lower():
            # Extract name from query (after "as" or "register")
            parts = query.lower().split(" as ")
            if len(parts) > 1:
                name = parts[1].strip()
            else:
                # Try to extract name after "register"
                parts = query.lower().split("register face")
                if len(parts) > 1:
                    name = parts[1].strip()
                    # Remove "for" or "of" prefix if present
                    for prefix in ["for ", "of "]:
                        if name.startswith(prefix):
                            name = name[len(prefix):]
                else:
                    name = "Unknown"
            
            # Initialize face detector with OpenCV
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            if face_cascade.empty():
                return "Error: Failed to load face detection model."
                
            # Initialize camera
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return "Error: Could not open camera."
                
            # Get frame dimensions
            ret, frame = cap.read()
            if not ret:
                cap.release()
                return "Error: Could not read from camera."
                
            height, width, _ = frame.shape
            
            # Setup parameters for face scanning UI
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
            
            print(f"\nRegistering face as: {name}")
            print("Please look at the camera. Press 's' to start scanning, 'q' to quit.")
            
            # Main loop
            while True:
                # Capture frame
                ret, frame = cap.read()
                if not ret:
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
                    minSize=(60, 80),  # Increase minimum face size
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
                        'image': face_img
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
                    import math
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
                            cv2.putText(output, "Press SPACE to save this face", (10, 60),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, success_color, 2)
                            cv2.putText(output, "Press 'r' to retake photo", (10, 90),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                        else:
                            cv2.putText(output, "Face saved successfully!", (10, 60),
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
                    if scan_complete and face_detected and not face_saved and len(detected_faces) > 0:
                        try:
                            # Show the detected face in a separate window
                            best_face = detected_faces[0]
                            face_preview = best_face['image'].copy()
                            cv2.imshow("Face to be saved", cv2.resize(face_preview, (300, 300)))
                            
                            print(f"\nSaving face as: {name}")
                            
                            # Save the face
                            import face_db_utils as db
                            saved_path = db.save_face_to_memory(best_face, name)
                            
                            face_saved = True
                            print(f"Face saved successfully as {name}")
                            print(f"Image saved to: {saved_path}")
                            
                            # Display success message for 2 seconds
                            success_img = np.zeros((200, 400, 3), np.uint8)
                            cv2.putText(success_img, "Face Saved Successfully!", (30, 80),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.8, success_color, 2)
                            cv2.putText(success_img, f"Name: {name}", (30, 120),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                            cv2.imshow("Success", success_img)
                            cv2.waitKey(2000)
                            
                            # Close preview windows
                            cv2.destroyWindow("Face to be saved")
                            cv2.destroyWindow("Success")
                            
                            # Return success message
                            break
                            
                        except Exception as e:
                            print(f"Error saving face: {e}")
                            import traceback
                            traceback.print_exc()
                            
                            # Show error message
                            error_img = np.zeros((200, 400, 3), np.uint8)
                            cv2.putText(error_img, "Error Saving Face", (30, 80),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                            cv2.putText(error_img, str(e)[:30], (30, 120),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                            cv2.imshow("Error", error_img)
                            cv2.waitKey(2000)
                            cv2.destroyWindow("Error")
            
            # Clean up
            cap.release()
            cv2.destroyAllWindows()
            
            # Return appropriate message
            if face_saved:
                return f"Successfully registered face as {name}!"
            else:
                return "Face registration was cancelled or failed."
            
        # Handle identification request
        elif any(kw in query.lower() for kw in ["identify", "recognize", "who", "scan"]):
            # Initialize face detector with OpenCV
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            if face_cascade.empty():
                return "Error: Failed to load face detection model."
                
            # Initialize camera
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return "Error: Could not open camera."
                
            # Get frame dimensions
            ret, frame = cap.read()
            if not ret:
                cap.release()
                return "Error: Could not read from camera."
                
            height, width, _ = frame.shape
            
            # Setup parameters for face scanning UI
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
            
            # UI colors
            circle_color = (0, 255, 0)  # Green
            scan_color = (0, 255, 255)  # Yellow
            text_color = (255, 255, 255)  # White
            face_color = (0, 0, 255)  # Red
            success_color = (0, 255, 0)  # Green
            
            print("\nIdentifying face...")
            print("Please look at the camera. Press 's' to start scanning, 'q' to quit.")
            
            # Start scanning immediately
            scan_start_time = time.time()
            
            # Main loop
            while True:
                # Capture frame
                ret, frame = cap.read()
                if not ret:
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
                    minSize=(60, 80),  # Increase minimum face size
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                # If no faces found, try with more lenient parameters
                if len(faces) == 0:
                    faces = face_cascade.detectMultiScale(
                        gray,
                        scaleFactor=1.2,  # More lenient scale factor
                        minNeighbors=3,   # Fewer neighbors required
                        minSize=(30, 30), # Smaller minimum face size
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
                        'image': face_img
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
                    import math
                    pulse_radius = scan_radius + int(10 * math.sin(time.time() * 10))
                    cv2.circle(overlay, (center_x, center_y), pulse_radius, scan_color, 1)
                    
                    # Check if face is detected during scan
                    if face_in_circle:
                        face_detected = True
                        detected_faces = current_faces
                        scan_complete = True
                        
                        # Try to identify the face
                        if not face_identified and len(detected_faces) > 0:
                            try:
                                # Show processing message
                                processing_img = np.zeros((100, 400, 3), np.uint8)
                                cv2.putText(processing_img, "Processing...", (150, 50),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                                cv2.imshow("Processing", processing_img)
                                cv2.waitKey(1)
                                
                                # Perform face matching
                                import face_db_utils as db
                                match_result = db.find_matching_face(detected_faces[0]['image'])
                                
                                # Close processing message
                                cv2.destroyWindow("Processing")
                                
                                if match_result['exists']:
                                    face_identified = True
                                    identified_person = match_result
                                    
                                    # Show the matched face
                                    if 'image_path' in match_result and os.path.exists(match_result['image_path']):
                                        try:
                                            matched_img = cv2.imread(match_result['image_path'])
                                            if matched_img is not None:
                                                cv2.imshow("Matched Face", cv2.resize(matched_img, (200, 200)))
                                        except Exception as e:
                                            print(f"Error displaying matched face: {e}")
                            except Exception as e:
                                print(f"Error during face identification: {e}")
                                import traceback
                                traceback.print_exc()
                
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
                            if 'id' in identified_person:
                                cv2.putText(output, f"ID: {identified_person['id']}", (10, 90),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, success_color, 2)
                            
                            # Add prompt to press any key
                            cv2.putText(output, "Press any key to continue", (10, height - 50),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
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
                
                # Check if scan is complete and face identified
                if scan_complete and face_detected:
                    if face_identified:
                        # Wait for a keypress to continue
                        if cv2.waitKey(3000) != -1:  # Wait up to 3 seconds for a key press
                            break
                    elif cv2.waitKey(100) & 0xFF == ord('r'):
                        # Switch to registration if 'r' is pressed
                        cv2.destroyAllWindows()
                        cap.release()
                        
                        # Ask for name
                        print("\nFace not recognized. Would you like to register it? (y/n)")
                        register_choice = input().strip().lower()
                        
                        if register_choice == 'y':
                            print("Enter name for this face: ")
                            new_name = input().strip()
                            if new_name:
                                return handle_face_command(f"register face as {new_name}")
                        
                        return "Face not recognized. Registration cancelled."
                
                # Check for key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s') and scan_start_time is None:
                    # Start scanning (though we auto-start in identification mode)
                    scan_start_time = time.time()
                    scan_radius = min_radius
                    growing = True
                    scan_complete = False
                    face_detected = False
                    detected_faces = []
                    face_identified = False
                    identified_person = None
                elif key == ord('r'):
                    # Reset scan
                    scan_start_time = time.time()
                    scan_radius = min_radius
                    growing = True
                    scan_complete = False
                    face_detected = False
                    detected_faces = []
                    face_identified = False
                    identified_person = None
            
            # Clean up
            cap.release()
            cv2.destroyAllWindows()
            
            # Return result based on identification
            if face_identified:
                confidence = identified_person.get('confidence', 1.0) * 100
                return f"Hello, {identified_person['name']}! Identified with {confidence:.1f}% confidence."
            elif face_detected:
                return "Face detected but not recognized in the database."
            else:
                return "No face detected. Please try again with better lighting or positioning."
        
        # Default fallback to direct method
        try:
            # Try to use the direct method
            import face_scan_tool
            result = face_scan_tool.process_face_directly(query)
            
            try:
                # Parse the JSON result
                data = json.loads(result)
                
                if "error" in data:
                    print(f"Error in face processing: {data['error']}")
                    raise Exception(data["error"])
                    
                # Check operation type
                if data.get("operation") == "register":
                    if data.get("success", False):
                        return f"Successfully registered face as {data.get('name')}!"
                    else:
                        return f"Failed to register face: {data.get('message', 'Unknown error')}"
                else:  # identify operation
                    if data.get("identified", False):
                        return f"Hello, {data.get('name')}! Identified with {data.get('confidence', '?')} confidence."
                    else:
                        return data.get('message', "Face detected but not recognized.")
            except json.JSONDecodeError:
                print(f"Error parsing JSON response: {result}")
                return "Failed to process face detection response."
                
        except Exception as e:
            print(f"Error in face processing: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"Error processing face: {str(e)}"
            
    except Exception as e:
        print(f"Error in face command handling: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error processing command: {str(e)}"

def main():
    # Load environment variables
    load_env()
    
    # Create or get memory file path
    memory_file_path = os.path.join(os.getcwd(), "system_memory.json")
    if not os.path.exists(memory_file_path):
        with open(memory_file_path, 'w') as f:
            json.dump({}, f)
    
    # Initialize face system
    face_system = FaceRecognitionSystem()
    
    # Show menu and handle user interactions
    show_interactive_menu(face_system)

def show_interactive_menu(face_system):
    """Display an interactive menu for face recognition operations"""
    print("\n====== Face Recognition System ======")
    print("Welcome to the Face Recognition System!")
    
    running = True
    while running:
        print("\n==== Main Menu ====")
        print("1. Scan/Identify Face (Headless Mode)")
        print("2. Register New Face (Interactive Preview)")
        print("3. List Saved Faces")
        print("4. Help")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '1':
            # Identify face using headless mode
            print("\n=== Scanning Face (Headless Mode) ===")
            print("Looking for faces... (please look at the camera)")
            try:
                # Use process_face_directly with headless=True
                import face_scan_tool
                result = face_scan_tool.process_face_directly("identify", headless=True) 
                data = json.loads(result)
                
                print("\n=== Face Scanning Result ===")
                if "error" in data:
                    print(f"Error: {data['error']}")
                elif data.get("identified", False):
                    print(f"Welcome, {data['name']}! (Confidence: {data['confidence']})")
                else:
                    print(data.get('message', "Face detected but not recognized."))
                    # Give option to register unrecognized face
                    if data.get("operation") == "identify" and not data.get("identified", False):
                        register = input("\nWould you like to register this face? (y/n): ").lower().strip()
                        if register == 'y':
                            # Switch to interactive registration mode (option 2)
                            print("\nSwitching to interactive registration mode...")
                            name = input("Enter name for this face: ").strip()
                            if name:
                                print(f"\nRegistering face as '{name}'...")
                                reg_result = face_scan_tool.process_face_directly(f"register face as {name}", headless=False)
                                reg_data = json.loads(reg_result)
                                if reg_data.get("success", False):
                                    print(f"Successfully registered face as {name}!")
                                    print(f"Image saved to: {reg_data.get('image_path', 'unknown')}")
                                else:
                                    print(f"Registration failed: {reg_data.get('message', 'Unknown error')}")
            except Exception as e:
                print(f"Error during face scanning: {str(e)}")
                import traceback
                traceback.print_exc()
            
        elif choice == '2':
            # Fully interactive registration with preview, dialog, retake and save options
            name = input("\nEnter name for the face: ")
            if name.strip():
                print("\n=== Registering Face (Interactive Mode) ===")
                print(f"Registering face as '{name}'...")
                print("\nInstructions:")
                print("- You will see a camera preview to help position your face")
                print("- Position your face in the scanning circle")
                print("- When your face is detected, press SPACE to capture")
                print("- Review the face preview and press SPACE to save or ESC to retake")
                print("- Press 'q' to cancel registration at any time")
                
                input("\nPress Enter to start the camera...")
                
                try:
                    # Use process_face_directly with full interactive preview mode
                    import face_scan_tool
                    result = face_scan_tool.process_face_directly(f"register face as {name}", headless=False)
                    data = json.loads(result)
                    
                    print("\n=== Registration Result ===")
                    if data.get("success", False):
                        print(f"✓ Successfully registered face as {name}!")
                        print(f"✓ Image saved to: {data.get('image_path', 'unknown')}")
                        
                        # Verify the image exists
                        image_path = data.get('image_path')
                        if image_path and os.path.exists(image_path):
                            print(f"✓ Image file verified: {os.path.basename(image_path)}")
                        else:
                            print("⚠ Note: Image file could not be verified")
                    else:
                        print(f"✗ Registration failed: {data.get('message', 'Unknown error')}")
                except Exception as e:
                    print(f"Error during face registration: {str(e)}")
                    import traceback
                    traceback.print_exc()
            else:
                print("Name cannot be empty.")
                
        elif choice == '3':
            # List faces
            print("\n=== Listing Saved Faces ===")
            try:
                # Direct database query
                faces = db.get_all_faces()
                if not faces or len(faces) == 0:
                    print("No faces found in database.")
                else:
                    print("\nFaces in database:")
                    print("-" * 80)
                    print(f"{'ID':<5} | {'Name':<20} | {'Image Path':<30} | {'Date':<20}")
                    print("-" * 80)
                    for face in faces:
                        face_id, name, image_path, timestamp = face
                        # Truncate image path if too long
                        if len(image_path) > 30:
                            image_path = "..." + image_path[-27:]
                        print(f"{face_id:<5} | {name:<20} | {image_path:<30} | {timestamp:<20}")
                    print("-" * 80)
                    print(f"Total faces: {len(faces)}")
            except Exception as e:
                print(f"Error listing faces: {str(e)}")
            
        elif choice == '4':
            # Help
            print("\n=== Face Recognition Help ===")
            print("This system allows you to:")
            print("- Scan and identify faces (headless mode)")
            print("- Register new faces with names (interactive mode)")
            print("- List all saved faces")
            print("\nOptions Explained:")
            print("1. Scan/Identify Face - Headless mode without camera preview")
            print("   • The system silently scans for faces and identifies them")
            print("   • No camera preview is shown (similar to Windows Hello)")
            print("   • Progress is shown in the terminal only")
            print("")
            print("2. Register New Face - Interactive mode with camera preview")
            print("   • Full camera preview is shown to help position face")
            print("   • Scanning circle guides face positioning")
            print("   • Press SPACE to capture the face")
            print("   • Review the captured face and confirm or retake")
            print("   • Face is saved to database with the provided name")
            
        elif choice == '5':
            # Exit
            print("Exiting Face Recognition System. Goodbye!")
            running = False
            
        else:
            print("Invalid choice. Please enter a number from 1 to 5.")
        
        if running:
            input("\nPress Enter to continue...")

# Only initialize the system when directly running the script
if __name__ == "__main__":
    main()

# Modified version of process_message that returns detailed results for the menu system
def handle_face_command_with_details(query: str):
    """Execute face recognition command with detailed response for menu display"""
    try:
        # Try to use the direct method first (faster, no MCP dependency)
        print("Attempting direct face processing...")
        import face_scan_tool
        result = face_scan_tool.process_face_directly(query)
        
        try:
            # Parse the JSON result
            data = json.loads(result)
            
            if "error" in data:
                print(f"Error in face processing: {data['error']}")
                # Fall back to traditional method
                return fallback_face_handler_with_details(query)
                
            # Check operation type and format a nice response
            if data.get("operation") == "register":
                if data.get("success", False):
                    image_path = data.get('image_path', 'unknown')
                    return {
                        "success": True,
                        "operation": "register",
                        "name": data.get('name'),
                        "image_path": image_path,
                        "message": f"✓ Successfully registered face as {data.get('name')}!",
                        "full_data": data
                    }
                else:
                    return {
                        "success": False,
                        "operation": "register",
                        "message": f"× Failed to register face: {data.get('message', 'Unknown error')}",
                        "full_data": data
                    }
            else:  # identify operation
                if data.get("identified", False):
                    image_path = data.get('image_path', 'unknown')
                    return {
                        "success": True,
                        "operation": "identify",
                        "name": data.get('name'),
                        "confidence": data.get('confidence', '?'),
                        "image_path": image_path,
                        "message": f"✓ Hello, {data.get('name')}! Identified with {data.get('confidence', '?')} confidence.",
                        "full_data": data
                    }
                else:
                    return {
                        "success": False,
                        "operation": "identify",
                        "message": data.get('message', "× Face detected but not recognized."),
                        "full_data": data
                    }
        except json.JSONDecodeError:
            print(f"Error parsing JSON response: {result}")
            # Fall back to traditional method
            return fallback_face_handler_with_details(query)
            
    except Exception as e:
        print(f"Error in direct face processing: {str(e)}")
        import traceback
        traceback.print_exc()
        # Fall back to traditional method
        return fallback_face_handler_with_details(query)

def fallback_face_handler_with_details(query: str):
    """Traditional face recognition handler as fallback with detailed response"""
    # This function would be similar to fallback_face_handler but returns structured data
    # For simplicity, we'll just return a basic response
    return {
        "success": False,
        "operation": "unknown",
        "message": "Face recognition failed. Please try again with better lighting or positioning.",
        "full_data": None
    }
