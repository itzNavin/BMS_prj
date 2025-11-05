"""
Face Recognition Service for Bus Management System
Integrates with face_recognition_package for real-time recognition via SocketIO
"""

import os
import sys
import base64
import binascii  # For base64 error handling
import io
import cv2
import numpy as np
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import face recognition system
try:
    from utils import BusFaceRecognitionService
    from backend.models import Student, Bus, StudentBusAssignment
    FACE_RECOGNITION_AVAILABLE = True
except (ImportError, AttributeError, Exception) as e:
    logging.warning(f"Face recognition not available: {e}")
    logging.warning("Face scanning will not work. App will run in basic mode.")
    FACE_RECOGNITION_AVAILABLE = False
    BusFaceRecognitionService = None

logger = logging.getLogger(__name__)


class BusRecognitionService:
    """
    Service for real-time face recognition in bus management system
    Handles SocketIO events and frame processing
    """
    
    def __init__(self):
        """Initialize the recognition service"""
        self.recognition_system = None
        self.active_sessions = {}  # {session_id: {'bus_id': int, 'driver_id': int, 'running': bool}}
        self.frame_processors = {}  # {session_id: threading.Thread}
        self._lock = threading.Lock()
        self._initialization_lock = threading.Lock()  # Lock for initialization
        self._initialized = False  # Track if already initialized
        # Cache student data to reduce database queries
        self._student_cache = {}  # {name: student_data}
        self._cache_ttl = 300  # Cache for 5 minutes
        self._cache_timestamp = {}  # {name: timestamp}
        
        # Database state tracking (with thread safety)
        self._db_empty = False  # Track if database is known to be empty
        self._last_refresh_attempt = 0  # Track last refresh attempt time
        self._refresh_cooldown = 60.0  # Cooldown period for refresh attempts (60 seconds)
        self._refresh_attempts = 0  # Track number of consecutive failed refresh attempts
        self._max_refresh_attempts = 3  # Max attempts before giving up
        self._db_state_lock = threading.Lock()  # Lock for database state variables
        
        # Reference to BusFaceRecognitionService for triggering refresh
        self.bus_service = None
        
        # Don't initialize here - lazy initialization on first use
        # This prevents multiple initializations
    
    def _ensure_initialized(self):
        """Lazy initialization - only initialize once"""
        if self._initialized and self.recognition_system:
            return True
        
        with self._initialization_lock:
            # Double-check after acquiring lock
            if self._initialized and self.recognition_system:
                return True
            
            if FACE_RECOGNITION_AVAILABLE:
                try:
                    # Initialize face recognition service only once
                    logger.info("Initializing face recognition service (first time)...")
                    if not self.bus_service:
                        self.bus_service = BusFaceRecognitionService()
                    self.recognition_system = self.bus_service.get_recognition_system()
                    if self.recognition_system:
                        self._initialized = True
                        logger.info("Face recognition service initialized successfully")
                    else:
                        logger.warning("Face recognition system not available")
                except Exception as e:
                    logger.error(f"Failed to initialize face recognition: {e}")
                    self.recognition_system = None
            
            return self._initialized
    
    def start_recognition(self, session_id: str, bus_id: int, driver_id: int) -> bool:
        """
        Start recognition session for a driver
        
        Args:
            session_id: Unique session identifier
            bus_id: Bus ID for checking assignments
            driver_id: Driver user ID
            
        Returns:
            True if started successfully
        """
        with self._lock:
            if session_id in self.active_sessions:
                logger.warning(f"Session {session_id} already active")
                return False
            
            self.active_sessions[session_id] = {
                'bus_id': bus_id,
                'driver_id': driver_id,
                'running': True,
                'last_recognition': None,
                'last_recognition_time': 0
            }
            
            logger.info(f"Started recognition session {session_id} for bus {bus_id}")
            return True
    
    def stop_recognition(self, session_id: str) -> bool:
        """
        Stop recognition session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if stopped successfully
        """
        with self._lock:
            if session_id not in self.active_sessions:
                return False
            
            self.active_sessions[session_id]['running'] = False
            del self.active_sessions[session_id]
            
            if session_id in self.frame_processors:
                # Wait for thread to finish
                thread = self.frame_processors[session_id]
                if thread.is_alive():
                    thread.join(timeout=2.0)
                del self.frame_processors[session_id]
            
            logger.info(f"Stopped recognition session {session_id}")
            return True
    
    def _get_student_from_cache_or_db(self, identity_name: str):
        """
        Get student data from cache or database with proper session management
        
        Args:
            identity_name: Student name
            
        Returns:
            Dict with student data or None (never returns SQLAlchemy object to avoid session issues)
        """
        from flask import current_app
        from backend.models import db
        
        # Check cache first
        current_time = time.time()
        if identity_name in self._student_cache:
            cache_time = self._cache_timestamp.get(identity_name, 0)
            if current_time - cache_time < self._cache_ttl:
                # Return cached data
                return self._student_cache[identity_name]
        
        # Not in cache or expired, query database with proper context
        try:
            # Use Flask app context to ensure proper session management
            from backend.app import app
            with app.app_context():
                student = Student.query.filter_by(name=identity_name).first()
                
                if student:
                    # Extract all needed data while session is active
                    student_data = {
                        'id': student.id,
                        'name': student.name,
                        'student_id': student.student_id,
                        'class_name': student.class_name,
                        'section': student.section
                    }
                    # Cache student data
                    self._student_cache[identity_name] = student_data
                    self._cache_timestamp[identity_name] = current_time
                    
                    # Ensure session is closed and connection returned to pool
                    db.session.close()
                    
                    return student_data
                
                # Ensure session is closed even if no student found
                db.session.close()
                return None
        except Exception as e:
            logger.error(f"Error querying student from database: {e}")
            # Ensure session is closed on error
            try:
                from backend.app import app
                from backend.models import db
                with app.app_context():
                    db.session.close()
            except:
                pass
            return None
    
    def _check_bus_assignment(self, student_data: dict, bus_id: int) -> bool:
        """
        Check if student is assigned to bus (always queries database directly)
        
        Args:
            student_data: Dict with student data (contains 'id')
            bus_id: Bus ID
            
        Returns:
            True if assigned
        """
        if not student_data or 'id' not in student_data:
            return False
        
        # Always query database directly to avoid session issues
        from backend.app import app
        from backend.models import db, StudentBusAssignment
        
        try:
            with app.app_context():
                assignment = StudentBusAssignment.query.filter_by(
                    student_id=student_data['id'],
                    bus_id=bus_id,
                    status='active'
                ).first()
                result = assignment is not None
                # Ensure session is closed and connection returned to pool
                db.session.close()
                return result
        except Exception as e:
            logger.error(f"Error checking bus assignment: {e}")
            # Ensure session is closed on error
            try:
                with app.app_context():
                    db.session.close()
            except:
                pass
            return False
    
    def process_frame(self, session_id: str, frame_data: str) -> Optional[Dict[str, Any]]:
        """
        Process a video frame for face recognition
        
        Args:
            session_id: Session identifier
            frame_data: Base64 encoded image data
            
        Returns:
            Recognition result dict or None
        """
        # Ensure recognition system is initialized (lazy initialization)
        if not self._ensure_initialized():
            return None
        
        if not self.recognition_system:
            return None
        
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        if not session['running']:
            return None
        
        # Prevent too frequent recognition (throttle - increased to reduce CPU load)
        current_time = time.time()
        if current_time - session.get('last_recognition_time', 0) < 3.0:  # Increased from 2.0 to 3.0 seconds
            return session.get('last_recognition')
        
        # Check if database is known to be empty - skip processing if so (thread-safe)
        with self._db_state_lock:
            if self._db_empty:
                # Only retry checking database every 60 seconds
                if current_time - self._last_refresh_attempt > self._refresh_cooldown:
                    self._db_empty = False  # Reset flag to allow retry
                    self._refresh_attempts = 0
                else:
                    # Skip processing to avoid infinite loop
                    return None
        
        try:
            # Decode base64 image with error handling
            try:
                # Extract base64 data (handle both 'data:image/jpeg;base64,...' and raw base64)
                if ',' in frame_data:
                    image_data = base64.b64decode(frame_data.split(',')[1])
                else:
                    image_data = base64.b64decode(frame_data)
            except (ValueError, TypeError, binascii.Error) as e:
                logger.warning(f"Invalid base64 image data: {e}")
                return None
            
            # Decode image with error handling
            try:
                nparr = np.frombuffer(image_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if frame is None:
                    logger.debug("Failed to decode image frame")
                    return None
                
                # Validate frame dimensions
                if frame.size == 0 or len(frame.shape) != 3:
                    logger.debug("Invalid frame dimensions")
                    return None
            except Exception as e:
                logger.warning(f"Error decoding image: {e}")
                return None
            
            # Process frame using recognition system
            # Note: This uses the internal method which may need adjustment
            try:
                result = self.recognition_system._process_frame_for_recognition(frame)
            except ValueError as e:
                # Handle empty database errors
                error_msg = str(e)
                if "No item found" in error_msg or "Nothing is found" in error_msg:
                    self._refresh_attempts += 1
                    self._last_refresh_attempt = current_time
                    
                    with self._db_state_lock:
                        if self._refresh_attempts >= self._max_refresh_attempts:
                            if not self._db_empty:  # Only log once
                                logger.warning("Face recognition database is empty. Please add student photos first.")
                            self._db_empty = True
                    
                    return None
                else:
                    # Re-raise other errors
                    raise
            
            if result and result.get('recognized'):
                # Map identity to student (with caching and proper session management)
                identity_name = result.get('identity', '')
                student_data = self._get_student_from_cache_or_db(identity_name)
                
                if student_data:
                    # Check bus assignment
                    bus_id = session['bus_id']
                    is_assigned = self._check_bus_assignment(student_data, bus_id)
                    
                    recognition_result = {
                        'recognized': True,
                        'student_id': student_data['id'],
                        'student_name': student_data['name'],
                        'student_id_display': student_data['student_id'],
                        'confidence': result.get('confidence', 0),
                        'is_assigned': is_assigned,
                        'class_name': student_data.get('class_name'),
                        'section': student_data.get('section')
                    }
                    
                    # Update session
                    session['last_recognition'] = recognition_result
                    session['last_recognition_time'] = current_time
                    
                    return recognition_result
            
            # Update session even if no recognition
            session['last_recognition'] = None
            session['last_recognition_time'] = current_time
            
            return None
            
        except ValueError as e:
            # Handle database empty errors gracefully (thread-safe)
            error_msg = str(e)
            if "No item found" in error_msg or "Nothing is found" in error_msg:
                with self._db_state_lock:
                    self._refresh_attempts += 1
                    self._last_refresh_attempt = time.time()
                    
                    if self._refresh_attempts >= self._max_refresh_attempts:
                        if not self._db_empty:  # Only log warning once
                            logger.warning("Face recognition database appears to be empty. Skipping recognition until photos are added.")
                            logger.warning("To use face recognition: Add students with photos via Admin panel first.")
                        self._db_empty = True
                
                return None
            else:
                logger.error(f"ValueError processing frame: {e}")
                return None
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return None
    
    def is_session_active(self, session_id: str) -> bool:
        """Check if session is active"""
        with self._lock:
            return session_id in self.active_sessions and self.active_sessions[session_id]['running']
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get session information"""
        with self._lock:
            return self.active_sessions.get(session_id)


# Global instance (singleton pattern)
_recognition_service = None
_recognition_service_lock = threading.Lock()

def get_recognition_service() -> BusRecognitionService:
    """Get or create global recognition service instance (singleton)"""
    global _recognition_service
    
    if _recognition_service is not None:
        return _recognition_service
    
    with _recognition_service_lock:
        # Double-check after acquiring lock (thread-safe singleton)
        if _recognition_service is not None:
            return _recognition_service
        
        _recognition_service = BusRecognitionService()
        return _recognition_service

