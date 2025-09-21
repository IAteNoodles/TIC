"""
Startup script for Whisper API Server
Run this to start the speech-to-text service
"""

import subprocess
import sys
import os

def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'whisper',
        'torch'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n🚨 Missing packages: {', '.join(missing_packages)}")
        print("Install them with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def start_server():
    """Start the Whisper API server"""
    print("🎤 Starting Whisper API Server...")
    print("📚 API Documentation will be available at: http://localhost:8006/docs")
    print("🌐 Frontend interface: whisper_frontend.html")
    print("=" * 60)
    
    try:
        # Run the server
        subprocess.run([
            sys.executable, 
            "whisper_server.py"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    print("🎤 Whisper API Server Setup")
    print("=" * 40)
    
    if check_requirements():
        print("\n✅ All requirements satisfied!")
        input("\nPress Enter to start the server...")
        start_server()
    else:
        print("\n❌ Please install missing requirements first")
        input("Press Enter to exit...")