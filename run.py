"""
Run script for Bus Management System
Convenience script to start the Flask application
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Import and run app
if __name__ == '__main__':
    from backend.app import app, create_tables, socketio
    import config
    
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
    print("="*60 + "\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=config.DEBUG)

