"""
Face recognition service integration for bus management system.
Provides easy interface to integrate face recognition with the bus management system.
"""

import os
import sys
import threading
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Add face_recognition_package to path
package_path = Path(__file__).parent.parent / "face_recognition_package"
if str(package_path) not in sys.path:
    sys.path.insert(0, str(package_path))

try:
    from advanced_realtime_recognition import FaceRecognitionSystem, RecognitionConfig
    FACE_RECOGNITION_AVAILABLE = True
except (ImportError, AttributeError, Exception) as e:
    logging.warning(f"Face recognition not available: {e}")
    logging.warning("Face recognition features will be disabled. App will run in basic mode.")
    FACE_RECOGNITION_AVAILABLE = False
    FaceRecognitionSystem = None
    RecognitionConfig = None

from .file_handler import copy_photos_to_face_db, refresh_face_recognition_db

logger = logging.getLogger(__name__)


class BusFaceRecognitionService:
    """Service class for integrating face recognition with bus management"""
    
    # Class-level singleton to prevent multiple system initializations
    _shared_system = None
    _shared_config = None
    _initialization_lock = threading.Lock()
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize face recognition service
        
        Args:
            config_path: Optional path to recognition_config.json
        """
        self.system = None
        self.config = None
        self.available = FACE_RECOGNITION_AVAILABLE
        
        if FACE_RECOGNITION_AVAILABLE and RecognitionConfig:
            if config_path and os.path.exists(config_path):
                self.config = RecognitionConfig.load(config_path)
            else:
                # Use default config
                default_config_path = package_path / "recognition_config.json"
                if default_config_path.exists():
                    self.config = RecognitionConfig.load(str(default_config_path))
                else:
                    self.config = RecognitionConfig(
                        db_path=str(package_path / "database"),
                        auto_refresh_database=True,
                        check_database_changes=True
                    )
            
            # CRITICAL FIX: Resolve relative db_path to absolute path
            if self.config and self.config.db_path:
                try:
                    # If db_path is relative, resolve it relative to package_path
                    db_path = Path(self.config.db_path)
                    if not db_path.is_absolute():
                        # Resolve relative to package_path (where config file is)
                        resolved_path = (package_path / self.config.db_path).resolve()
                        self.config.db_path = str(resolved_path)
                    else:
                        self.config.db_path = str(db_path.resolve())
                    
                    # Ensure the directory exists or can be created
                    db_path_obj = Path(self.config.db_path)
                    if not db_path_obj.exists():
                        try:
                            db_path_obj.mkdir(parents=True, exist_ok=True)
                            logger.info(f"Created face recognition database directory: {self.config.db_path}")
                        except (OSError, PermissionError) as e:
                            logger.error(f"Cannot create database directory {self.config.db_path}: {e}")
                    
                    logger.info(f"Face recognition database path: {self.config.db_path}")
                except Exception as e:
                    logger.error(f"Error resolving database path: {e}")
                    # Fallback to default path
                    default_path = package_path / "database"
                    self.config.db_path = str(default_path.resolve())
                    logger.warning(f"Using default database path: {self.config.db_path}")
            
            # Store config at class level for sharing
            if self.config:
                BusFaceRecognitionService._shared_config = self.config
    
    def add_student_photos(self, photos: list, student_name: str) -> bool:
        """
        Add student photos to face recognition database
        
        Args:
            photos: List of photo file paths
            student_name: Student name
            
        Returns:
            True if successful
        """
        try:
            face_db_base = str(package_path / "database")
            copied_paths = copy_photos_to_face_db(photos, student_name, face_db_base)
            
            if copied_paths:
                # Trigger refresh using the proper method (ensures system is initialized)
                self.trigger_database_refresh()
                logger.info(f"Added {len(copied_paths)} photos for {student_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding student photos: {e}")
            return False
    
    def remove_student_photos(self, student_name: str) -> bool:
        """
        Remove student photos from face recognition database
        
        Args:
            student_name: Student name
            
        Returns:
            True if successful
        """
        try:
            from .file_handler import delete_student_from_face_db
            face_db_base = str(package_path / "database")
            deleted = delete_student_from_face_db(student_name, face_db_base)
            
            if deleted:
                # Trigger refresh using the proper method (ensures system is initialized)
                self.trigger_database_refresh()
            
            return deleted
        except Exception as e:
            logger.error(f"Error removing student photos: {e}")
            return False
    
    def get_recognition_system(self) -> Optional[FaceRecognitionSystem]:
        """
        Get or create face recognition system instance (singleton pattern)
        
        Returns:
            FaceRecognitionSystem instance or None if not available
        """
        if not FaceRecognitionSystem:
            logger.error("Face recognition system not available")
            return None
        
        # Use class-level singleton to prevent multiple initializations
        if BusFaceRecognitionService._shared_system is not None:
            self.system = BusFaceRecognitionService._shared_system
            return self.system
        
        # Initialize only once with lock
        with BusFaceRecognitionService._initialization_lock:
            # Double-check after acquiring lock
            if BusFaceRecognitionService._shared_system is not None:
                self.system = BusFaceRecognitionService._shared_system
                return self.system
            
            # Use shared config or instance config
            config_to_use = BusFaceRecognitionService._shared_config or self.config
            
            if config_to_use:
                try:
                    logger.info("Creating face recognition system (singleton, first time only)...")
                    BusFaceRecognitionService._shared_system = FaceRecognitionSystem(config_to_use)
                    self.system = BusFaceRecognitionService._shared_system
                    logger.info("Face recognition system initialized successfully (shared instance)")
                except Exception as e:
                    logger.error(f"Failed to initialize face recognition system: {e}")
                    return None
            else:
                logger.error("No configuration available for face recognition system")
                return None
        
        return self.system
    
    def trigger_database_refresh(self) -> bool:
        """
        Manually trigger face recognition database refresh
        
        Returns:
            True if refresh was triggered
        """
        # Get the system instance (will initialize if needed)
        system = self.get_recognition_system()
        
        if system:
            logger.info("Triggering face recognition database refresh...")
            result = refresh_face_recognition_db(system)
            logger.info("Face recognition database refresh triggered successfully")
            return result
        else:
            logger.warning("Face recognition system not initialized. Database will auto-refresh on next use.")
            return True

