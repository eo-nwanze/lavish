#!/usr/bin/env python3
"""
Simple HTTP Server for Lavish Library Client Demo
Exposes the account system demo for client viewing
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

# Configuration
PORT = 8080
DEMO_DIR = Path(__file__).parent

class DemoHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler to serve demo files with proper MIME types"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DEMO_DIR), **kwargs)
    
    def end_headers(self):
        # Add CORS headers for cross-origin requests
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        # Redirect root to client demo
        if self.path == '/':
            self.send_response(302)
            self.send_header('Location', '/client-demo.html')
            self.end_headers()
            return
        
        # Handle account system redirect
        if self.path == '/account':
            self.send_response(302)
            self.send_header('Location', '/debug-account-system.html')
            self.end_headers()
            return
            
        super().do_GET()

def get_local_ip():
    """Get local IP address for network access"""
    import socket
    try:
        # Connect to a remote address to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "127.0.0.1"

def main():
    """Start the demo server"""
    
    # Change to demo directory
    os.chdir(DEMO_DIR)
    
    # Check if required files exist
    required_files = [
        'client-demo.html',
        'debug-account-system.html',
        'sections/enhanced-account.liquid'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPlease ensure all demo files are present.")
        return
    
    # Start server
    try:
        with socketserver.TCPServer(("", PORT), DemoHTTPRequestHandler) as httpd:
            local_ip = get_local_ip()
            
            print("🚀 Lavish Library Demo Server Started!")
            print("=" * 50)
            print(f"📍 Local Access:    http://127.0.0.1:{PORT}")
            print(f"🌐 Network Access:  http://{local_ip}:{PORT}")
            print("=" * 50)
            print("\n📋 Available URLs:")
            print(f"   🏠 Demo Home:     http://127.0.0.1:{PORT}/")
            print(f"   👤 Account System: http://127.0.0.1:{PORT}/account")
            print(f"   🔧 Debug Version:  http://127.0.0.1:{PORT}/debug-account-system.html")
            print("\n💡 Share the Network Access URL with clients for remote viewing")
            print("⏹️  Press Ctrl+C to stop the server")
            print("=" * 50)
            
            # Auto-open browser
            try:
                webbrowser.open(f'http://127.0.0.1:{PORT}/')
                print("🌐 Opening demo in your default browser...")
            except:
                pass
            
            # Start serving
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo server stopped by user")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {PORT} is already in use.")
            print("   Try stopping other servers or use a different port.")
        else:
            print(f"❌ Server error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
