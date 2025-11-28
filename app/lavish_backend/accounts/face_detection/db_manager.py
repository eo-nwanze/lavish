import argparse
import sys
import face_db_utils as db
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description='SQLite Face Database Manager')
    parser.add_argument('command', choices=['init', 'list', 'get', 'update', 'delete', 'search', 'stats'], 
                        help='Command to execute')
    parser.add_argument('--id', type=int, help='Face ID for get/update/delete operations')
    parser.add_argument('--name', type=str, help='Name for update/filter operations')
    parser.add_argument('--limit', type=int, default=10, help='Limit for list operations')
    parser.add_argument('--query', type=str, help='Search query for search operation')
    
    args = parser.parse_args()
    
    if args.command == 'init':
        db.create_db_tables()
        print("Database initialized successfully")
    elif args.command == 'list':
        list_faces(args.limit, args.name)
    elif args.command == 'get':
        if not args.id:
            print("Error: --id parameter is required for get command")
            sys.exit(1)
        get_face_details(args.id)
    elif args.command == 'update':
        if not args.id:
            print("Error: --id parameter is required for update command")
            sys.exit(1)
        success, message = db.update_face_name(args.id, args.name)
        print(message)
    elif args.command == 'delete':
        if not args.id:
            print("Error: --id parameter is required for delete command")
            sys.exit(1)
        success, message = db.delete_face(args.id)
        print(message)
    elif args.command == 'search':
        if not args.query:
            print("Error: --query parameter is required for search command")
            sys.exit(1)
        search_faces(args.query)
    elif args.command == 'stats':
        show_stats()
        
def list_faces(limit=10, name=None):
    """List all faces in the database, optionally filtered by name"""
    faces = db.get_all_faces()
    
    # Apply name filter if provided
    if name:
        faces = [face for face in faces if name.lower() in face[1].lower()]
    
    # Apply limit
    faces = faces[:limit]
    
    if not faces:
        print("No faces found in database.")
        return
    
    print(f"Faces in database ({len(faces)} results):")
    for face in faces:
        print(f"ID: {face[0]}, Name: {face[1]}, Image: {face[2]}, Time: {face[3]}")

def get_face_details(face_id):
    """Get detailed information about a specific face"""
    face = db.get_face_details(face_id)
    
    if not face:
        print(f"No face found with ID {face_id}")
        return
    
    print(f"Face Details (ID: {face['id']}):")
    print(f"Name: {face['name']}")
    print(f"Image Path: {face['image_path']}")
    print(f"First Detected: {face['timestamp']}")
    print(f"Face Hash: {face['face_hash']}")
    print(f"Position: x={face['x']}, y={face['y']}, width={face['width']}, height={face['height']}")
    
    if face['meta_data']:
        print("\nMeta Data:")
        for key, value in face['meta_data'].items():
            print(f"  {key}: {value}")
    
    if face['detections']:
        print(f"\nDetection History ({len(face['detections'])} events):")
        for det in face['detections'][:5]:  # Show only the 5 most recent detections
            print(f"  {det[0]} - {det[1]}")
        
        if len(face['detections']) > 5:
            print(f"  ... and {len(face['detections']) - 5} more detections")

def search_faces(query):
    """Search for faces by name"""
    faces = db.get_all_faces()
    
    # Apply query filter
    matches = [face for face in faces if query.lower() in face[1].lower()]
    
    if not matches:
        print(f"No faces found matching query: {query}")
        return
    
    print(f"Found {len(matches)} faces matching '{query}':")
    for face in matches:
        print(f"ID: {face[0]}, Name: {face[1]}, Image: {face[2]}, Time: {face[3]}")

def show_stats():
    """Show database statistics"""
    faces = db.get_all_faces()
    
    if not faces:
        print("No faces in database.")
        return
    
    # Count unique names
    names = {}
    for face in faces:
        name = face[1]
        if name in names:
            names[name] += 1
        else:
            names[name] = 1
    
    # Get latest detection
    latest_face = faces[0] if faces else None
    
    print("Database Statistics:")
    print(f"Total Faces: {len(faces)}")
    print(f"Latest Detection: {latest_face[3] if latest_face else 'None'}")
    
    if names:
        print("\nDetected Individuals:")
        for name, count in sorted(names.items(), key=lambda x: x[1], reverse=True):
            print(f"  {name}: {count} {'faces' if count > 1 else 'face'}")

if __name__ == "__main__":
    main()
