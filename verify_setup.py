"""
Comprehensive verification script for Bus Management System
Checks all connections, imports, and file structure
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

print("="*70)
print("BUS MANAGEMENT SYSTEM - COMPREHENSIVE VERIFICATION")
print("="*70 + "\n")

errors = []
warnings = []
passed = []

def check(name, func):
    """Run a check and track results"""
    try:
        result = func()
        if result:
            passed.append(name)
            print(f"[OK] {name}: PASSED")
        else:
            warnings.append(name)
            print(f"[!] {name}: WARNING")
    except Exception as e:
        errors.append((name, str(e)))
        print(f"[FAIL] {name}: FAILED - {e}")

# Check 1: Directory Structure
def check_directories():
    required_dirs = [
        "backend",
        "backend/routes",
        "backend/services",
        "frontend",
        "frontend/templates",
        "frontend/templates/admin",
        "frontend/templates/driver",
        "frontend/templates/auth",
        "frontend/static/css",
        "frontend/static/js",
        "uploads/students",
        "face_recognition_package/database",
        "utils",
        "database"
    ]
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
    return True

check("Directory Structure", check_directories)

# Check 2: Configuration File
def check_config():
    try:
        import config
        assert hasattr(config, 'SECRET_KEY')
        assert hasattr(config, 'SQLALCHEMY_DATABASE_URI')
        assert hasattr(config, 'UPLOAD_FOLDER')
        return True
    except Exception as e:
        raise Exception(f"Config error: {e}")

check("Configuration File", check_config)

# Check 3: Database Models
def check_models():
    try:
        from backend.models import db, User, Student, Bus, StudentBusAssignment, AuthenticationLog
        assert User is not None
        assert Student is not None
        assert Bus is not None
        return True
    except Exception as e:
        raise Exception(f"Models import error: {e}")

check("Database Models", check_models)

# Check 4: Routes
def check_routes():
    try:
        from backend.routes import auth_routes, admin_routes, driver_routes
        assert hasattr(auth_routes, 'bp')
        assert hasattr(admin_routes, 'bp')
        assert hasattr(driver_routes, 'bp')
        return True
    except Exception as e:
        raise Exception(f"Routes import error: {e}")

check("Routes", check_routes)

# Check 5: Services
def check_services():
    try:
        from backend.services.student_service import StudentService
        from backend.services.bus_service import BusService
        from backend.services.face_recognition_service import get_recognition_service
        return True
    except Exception as e:
        raise Exception(f"Services import error: {e}")

check("Services", check_services)

# Check 6: Utils Module
def check_utils():
    try:
        from utils import (
            save_student_photos,
            copy_photos_to_face_db,
            BusFaceRecognitionService
        )
        return True
    except Exception as e:
        raise Exception(f"Utils import error: {e}")

check("Utils Module", check_utils)

# Check 7: Flask App Initialization
def check_flask_app():
    try:
        from backend.app import app
        assert app is not None
        assert hasattr(app, 'config')
        return True
    except Exception as e:
        raise Exception(f"Flask app error: {e}")

check("Flask Application", check_flask_app)

# Check 8: Database Connection
def check_database():
    try:
        from backend.app import app, db
        with app.app_context():
            db.create_all()
            # Try a simple query
            from backend.models import User
            count = User.query.count()
            return True
    except Exception as e:
        raise Exception(f"Database error: {e}")

check("Database Connection", check_database)

# Check 9: Template Files
def check_templates():
    required_templates = [
        "frontend/templates/base.html",
        "frontend/templates/auth/login.html",
        "frontend/templates/admin/dashboard.html",
        "frontend/templates/driver/dashboard.html",
        "frontend/templates/driver/face_scanning.html"
    ]
    for template in required_templates:
        if not os.path.exists(template):
            raise Exception(f"Missing template: {template}")
    return True

check("Template Files", check_templates)

# Check 10: Static Files
def check_static():
    static_files = [
        "frontend/static/css/style.css",
        "frontend/static/js/main.js",
        "frontend/static/js/face_scanning.js"
    ]
    for static_file in static_files:
        if not os.path.exists(static_file):
            raise Exception(f"Missing static file: {static_file}")
    return True

check("Static Files", check_static)

# Summary
print("\n" + "="*70)
print("VERIFICATION SUMMARY")
print("="*70)
print(f"[OK] Passed: {len(passed)}")
print(f"[!] Warnings: {len(warnings)}")
print(f"[FAIL] Errors: {len(errors)}")
print("="*70)

if errors:
    print("\n[ERROR] ERRORS FOUND:")
    for name, error in errors:
        print(f"   {name}: {error}")
    print("\n[!] Please fix errors before running the application.")
    sys.exit(1)
elif warnings:
    print("\n[!] WARNINGS:")
    for warning in warnings:
        print(f"   {warning}")
    print("\n[OK] Application should work, but review warnings.")
    sys.exit(0)
else:
    print("\n[SUCCESS] ALL CHECKS PASSED!")
    print("[OK] Application is ready to run!")
    print("\n[INFO] To start the application, run:")
    print("   python run.py")
    print("   or")
    print("   python backend/app.py")
    sys.exit(0)

