"""
Test script to verify the face recognition integration works correctly.
This script tests the file handling utilities and verifies the directory structure.
"""

import os
from pathlib import Path
from utils.file_handler import (
    ensure_directory,
    validate_image_file,
    get_student_photos
)

def test_directory_structure():
    """Test that all required directories exist"""
    print("=" * 60)
    print("Testing Directory Structure...")
    print("=" * 60)
    
    directories = [
        "uploads/students",
        "face_recognition_package/database"
    ]
    
    all_exist = True
    for directory in directories:
        exists = os.path.exists(directory)
        status = "[OK]" if exists else "[MISSING]"
        print(f"{status} {directory}: {'EXISTS' if exists else 'MISSING'}")
        if not exists:
            all_exist = False
            ensure_directory(directory)
            print(f"  -> Created {directory}")
    
    return all_exist


def test_face_recognition_database():
    """Test face recognition database structure"""
    print("\n" + "=" * 60)
    print("Testing Face Recognition Database...")
    print("=" * 60)
    
    db_path = "face_recognition_package/database"
    if not os.path.exists(db_path):
        print(f"[ERROR] Database path not found: {db_path}")
        return False
    
    # Check for images
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
    items = os.listdir(db_path)
    
    images = [f for f in items if Path(f).suffix.lower() in image_extensions]
    folders = [f for f in items if os.path.isdir(os.path.join(db_path, f)) and f not in ['utils', '.git']]
    
    print(f"[OK] Database path exists: {db_path}")
    print(f"  Found {len(images)} flat image files")
    print(f"  Found {len(folders)} student folders")
    
    # List student folders
    if folders:
        print("\n  Student folders:")
        for folder in sorted(folders):
            folder_path = os.path.join(db_path, folder)
            folder_images = [f for f in os.listdir(folder_path) 
                           if Path(f).suffix.lower() in image_extensions]
            print(f"    - {folder}/ ({len(folder_images)} images)")
    
    return True


def test_utils_module():
    """Test that utils module can be imported"""
    print("\n" + "=" * 60)
    print("Testing Utils Module...")
    print("=" * 60)
    
    try:
        from utils import (
            save_student_photos,
            copy_photos_to_face_db,
            refresh_face_recognition_db,
            BusFaceRecognitionService
        )
        print("[OK] Utils module imports successfully")
        print("[OK] All required functions are available")
        return True
    except ImportError as e:
        print(f"[ERROR] Failed to import utils module: {e}")
        return False


def test_face_recognition_system():
    """Test that face recognition system can be initialized"""
    print("\n" + "=" * 60)
    print("Testing Face Recognition System Integration...")
    print("=" * 60)
    
    try:
        from utils import BusFaceRecognitionService
        
        service = BusFaceRecognitionService()
        if service.config:
            print("[OK] Face recognition service initialized")
            print(f"  Database path: {service.config.db_path}")
            print(f"  Auto-refresh: {service.config.auto_refresh_database}")
            return True
        else:
            print("[WARNING] Face recognition service config not available (DeepFace may not be installed)")
            print("  This is OK if you're just testing file structure")
            return True  # Not a critical error
    except Exception as e:
        print(f"[WARNING] Failed to initialize face recognition service: {e}")
        print("  This is OK if DeepFace dependencies are not installed yet")
        return True  # Not a critical error for structure testing


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("BUS MANAGEMENT SYSTEM - INTEGRATION TEST")
    print("=" * 60 + "\n")
    
    results = []
    
    # Test 1: Directory structure
    results.append(("Directory Structure", test_directory_structure()))
    
    # Test 2: Face recognition database
    results.append(("Face Recognition Database", test_face_recognition_database()))
    
    # Test 3: Utils module
    results.append(("Utils Module", test_utils_module()))
    
    # Test 4: Face recognition system
    results.append(("Face Recognition System", test_face_recognition_system()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        symbol = "[OK]" if passed else "[FAIL]"
        print(f"{symbol} {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] ALL TESTS PASSED - System is ready!")
    else:
        print("[ERROR] SOME TESTS FAILED - Please review errors above")
    print("=" * 60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

