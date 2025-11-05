"""
Run script for Bus Management System
Convenience script to start the Flask application
"""

import sys
import os
import signal
import threading
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Global reference for cleanup
_socketio_instance = None
_recognition_service = None
_shutdown_event = threading.Event()

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    # Prevent multiple calls
    if _shutdown_event.is_set():
        print("\n⚠️  Force exit...")
        os._exit(1)
    
    _shutdown_event.set()
    print("\n\n🛑 Shutting down gracefully...")
    
    # Stop all recognition sessions
    try:
        from backend.services.face_recognition_service import get_recognition_service
        recognition_service = get_recognition_service()
        recognition_service.stop_all_sessions()
        print("✅ Stopped all recognition sessions")
    except Exception as e:
        print(f"⚠️  Error stopping recognition sessions: {e}")
    
    # Exit gracefully - use os._exit to force immediate termination
    print("✅ Shutdown complete")
    os._exit(0)

# Import and run app
if __name__ == '__main__':
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    from backend.app import app, create_tables, socketio
    import config
    
    _socketio_instance = socketio
    
    # Create tables on first run
    print("Initializing database...")
    create_tables()
    
    # Run application
    print("\n" + "="*60)
    print("🚌 Bus Management System Starting...")
    print("="*60)
    print(f"📁 Database: {config.SQLALCHEMY_DATABASE_URI}")
    print(f"🌐 Running on: http://localhost:5000")
    print("="*60)
    print("\n📝 Default Login Credentials:")
    print("   Admin: username='admin', password='admin123'")
    print("   Driver: username='driver1', password='driver123'")
    print("="*60)
    print("\n💡 Press Ctrl+C to stop the server\n")
    
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=config.DEBUG, use_reloader=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    except SystemExit:
        # Already handled by signal handler
        pass

