"""
File handling utilities for bus management system.
Handles copying student photos between uploads and face recognition database.
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def ensure_directory(path: str) -> None:
    """Ensure a directory exists, create if it doesn't"""
    Path(path).mkdir(parents=True, exist_ok=True)


def save_student_photos(photos: List, student_id: str, uploads_base: str = "uploads/students") -> List[str]:
    """
    Save uploaded photos to uploads/students/student_id/ directory
    
    Args:
        photos: List of uploaded photo files (file objects or file paths)
        student_id: Student ID for organizing photos
        uploads_base: Base directory for uploads
        
    Returns:
        List of saved file paths
    """
    save_path = os.path.join(uploads_base, str(student_id))
    ensure_directory(save_path)
    
    saved_paths = []
    for idx, photo in enumerate(photos, 1):
        # Handle both file objects and file paths
        if hasattr(photo, 'save'):
            # Flask file upload object
            filename = f"photo{idx}.jpg"
            filepath = os.path.join(save_path, filename)
            photo.save(filepath)
            saved_paths.append(filepath)
        elif isinstance(photo, str):
            # File path string
            if os.path.exists(photo):
                filename = f"photo{idx}{Path(photo).suffix}"
                filepath = os.path.join(save_path, filename)
                shutil.copy2(photo, filepath)
                saved_paths.append(filepath)
        else:
            logger.warning(f"Unknown photo type: {type(photo)}")
    
    logger.info(f"Saved {len(saved_paths)} photos to {save_path}")
    return saved_paths


def copy_photos_to_face_db(photos: List[str], student_name: str, 
                           face_db_base: str = "face_recognition_package/database") -> List[str]:
    """
    Copy photos from uploads to face recognition database.
    Organizes photos by student_name in face_recognition_package/database/student_name/
    
    Args:
        photos: List of photo file paths (from uploads/students/)
        student_name: Student name for organizing in face recognition DB
        face_db_base: Base directory for face recognition database
        
    Returns:
        List of copied file paths in face recognition database
    """
    # Sanitize student name for folder name (remove invalid characters)
    safe_name = "".join(c for c in student_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_name = safe_name.replace(' ', '_')  # Replace spaces with underscores
    
    face_db_path = os.path.join(face_db_base, safe_name)
    ensure_directory(face_db_path)
    
    copied_paths = []
    for idx, photo_path in enumerate(photos, 1):
        if not os.path.exists(photo_path):
            logger.warning(f"Photo not found: {photo_path}")
            continue
        
        # Get file extension
        ext = Path(photo_path).suffix.lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.bmp']:
            logger.warning(f"Unsupported image format: {ext}")
            continue
        
        # Copy with numbered filename
        filename = f"photo{idx}{ext}"
        dest_path = os.path.join(face_db_path, filename)
        
        try:
            shutil.copy2(photo_path, dest_path)
            copied_paths.append(dest_path)
            logger.info(f"Copied {photo_path} -> {dest_path}")
        except Exception as e:
            logger.error(f"Error copying {photo_path}: {e}")
    
    logger.info(f"Copied {len(copied_paths)} photos to {face_db_path}")
    return copied_paths


def refresh_face_recognition_db(system_instance=None) -> bool:
    """
    Trigger face recognition database refresh.
    This should be called after adding new photos to the face recognition database.
    
    Args:
        system_instance: Optional FaceRecognitionSystem instance to trigger refresh
        
    Returns:
        True if refresh was triggered successfully
    """
    if system_instance:
        # Clear DeepFace pickle cache files to force complete refresh
        db_path = system_instance.config.db_path if hasattr(system_instance, 'config') and system_instance.config else None
        if db_path and os.path.exists(db_path):
            # Find and delete pickle files (DeepFace embeddings cache)
            import glob
            pkl_files = glob.glob(os.path.join(db_path, '*.pkl'))
            for pkl_file in pkl_files:
                try:
                    os.remove(pkl_file)
                    logger.info(f"Deleted cached embeddings file: {pkl_file}")
                except Exception as e:
                    logger.warning(f"Could not delete cache file {pkl_file}: {e}")
        
        # Reset database state to force full refresh
        system_instance._pending_refresh = True
        system_instance._db_initialized = False  # Force re-initialization
        system_instance._db_file_count = 0  # Reset file count to trigger change detection
        system_instance._db_empty = False  # Reset empty flag
        system_instance._refresh_attempted = False  # Reset refresh attempt flag
        system_instance._refresh_fail_count = 0  # Reset failure count
        system_instance._last_db_check_time = 0  # Reset check time to force immediate check
        
        logger.info("Face recognition database refresh triggered - database state reset")
        logger.info("Database will be refreshed on next frame processing (embeddings will be rebuilt)")
        return True
    else:
        # Database will auto-refresh on next recognition cycle
        logger.info("Face recognition database will auto-refresh on next recognition")
        return True


def get_student_photos(student_id: str, uploads_base: str = "uploads/students") -> List[str]:
    """
    Get all photo paths for a student from uploads directory
    
    Args:
        student_id: Student ID
        uploads_base: Base directory for uploads
        
    Returns:
        List of photo file paths
    """
    student_dir = os.path.join(uploads_base, str(student_id))
    if not os.path.exists(student_dir):
        return []
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
    photos = [
        os.path.join(student_dir, f)
        for f in os.listdir(student_dir)
        if Path(f).suffix.lower() in image_extensions
    ]
    
    return sorted(photos)


def delete_student_photos(student_id: str, uploads_base: str = "uploads/students") -> bool:
    """
    Delete all photos for a student from uploads directory
    
    Args:
        student_id: Student ID
        uploads_base: Base directory for uploads
        
    Returns:
        True if deleted successfully
    """
    student_dir = os.path.join(uploads_base, str(student_id))
    if os.path.exists(student_dir):
        try:
            shutil.rmtree(student_dir)
            logger.info(f"Deleted photos for student {student_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting photos for student {student_id}: {e}")
            return False
    return True


def delete_student_from_face_db(student_name: str, 
                                  face_db_base: str = "face_recognition_package/database") -> bool:
    """
    Delete student folder from face recognition database
    
    Args:
        student_name: Student name
        face_db_base: Base directory for face recognition database
        
    Returns:
        True if deleted successfully
    """
    safe_name = "".join(c for c in student_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_name = safe_name.replace(' ', '_')
    
    face_db_path = os.path.join(face_db_base, safe_name)
    if os.path.exists(face_db_path):
        try:
            shutil.rmtree(face_db_path)
            logger.info(f"Deleted {face_db_path} from face recognition database")
            return True
        except Exception as e:
            logger.error(f"Error deleting {face_db_path}: {e}")
            return False
    return True


def validate_image_file(file_path: str) -> bool:
    """
    Validate that a file is a valid image
    
    Args:
        file_path: Path to file
        
    Returns:
        True if valid image file
    """
    if not os.path.exists(file_path):
        return False
    
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
    ext = Path(file_path).suffix.lower()
    return ext in valid_extensions

