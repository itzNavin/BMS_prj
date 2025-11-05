"""
Utilities module for bus management system
"""

from .file_handler import (
    save_student_photos,
    copy_photos_to_face_db,
    refresh_face_recognition_db,
    get_student_photos,
    delete_student_photos,
    delete_student_from_face_db,
    validate_image_file
)

# Try to import face recognition service (may fail on Python 3.13 due to compatibility)
try:
    from .face_recognition_service import BusFaceRecognitionService
    FACE_RECOGNITION_AVAILABLE = True
except (ImportError, AttributeError, Exception) as e:
    import logging
    logging.warning(f"Face recognition service not available: {e}")
    # Create a dummy class so imports don't fail
    class BusFaceRecognitionService:
        def __init__(self, *args, **kwargs):
            self.available = False
            self.config = None
            self.system = None
        def add_student_photos(self, *args, **kwargs):
            return False
        def remove_student_photos(self, *args, **kwargs):
            return False
        def get_recognition_system(self):
            return None
        def trigger_database_refresh(self, *args, **kwargs):
            return False
    FACE_RECOGNITION_AVAILABLE = False

__all__ = [
    'save_student_photos',
    'copy_photos_to_face_db',
    'refresh_face_recognition_db',
    'get_student_photos',
    'delete_student_photos',
    'delete_student_from_face_db',
    'validate_image_file',
    'BusFaceRecognitionService',
    'FACE_RECOGNITION_AVAILABLE'
]

