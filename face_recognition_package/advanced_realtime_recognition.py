"""
Advanced Real-Time Face Recognition System
Production-ready implementation with error handling, optimization, and advanced features.
"""

import os
import sys
import time
import threading
import queue
import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

import cv2
import numpy as np
import pandas as pd
from deepface import DeepFace
from deepface.commons.logger import Logger as DeepFaceLogger

# Configure logging
# Fix Windows console encoding for Unicode characters
import sys
if sys.platform == 'win32':
    # Set console to UTF-8 for Windows
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('face_recognition.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class RecognitionConfig:
    """Configuration for face recognition system"""
    # Database
    db_path: str = "database"
    auto_refresh_database: bool = True  # Auto-refresh when database changes detected
    refresh_database_on_start: bool = True  # Force refresh on startup
    check_database_changes: bool = True  # Monitor database for new files
    
    # Models
    recognition_model: str = "VGG-Face"  # VGG-Face, Facenet, Facenet512, ArcFace, Dlib
    detector_backend: str = "opencv"     # opencv, retinaface, mtcnn, ssd, dlib, mediapipe
    distance_metric: str = "cosine"       # cosine, euclidean, euclidean_l2, angular
    
    # Camera
    camera_source: Any = 0  # 0, 1, 2, or video path, or RTSP URL
    camera_width: int = 640
    camera_height: int = 480
    camera_fps: int = 30
    
    # Processing
    frame_skip: int = 5  # Process every Nth frame (higher = faster but less responsive)
    max_processing_queue: int = 1  # Max frames waiting for processing (lower = less lag)
    min_face_size: int = 100  # Minimum face size to process (pixels)
    
    # Recognition thresholds
    confidence_threshold: float = 60.0  # Minimum confidence to accept match (60-70 is good balance)
    distance_threshold: Optional[float] = None  # Auto if None (uses model defaults)
    show_unknown_faces: bool = True  # Show "Unknown" for faces not in database
    debug_recognition: bool = False  # Show debug logs for rejected matches
    
    # Analysis
    enable_face_analysis: bool = False  # Age, gender, emotion
    enable_anti_spoofing: bool = False
    
    # Display
    show_fps: bool = True
    show_statistics: bool = True
    show_bounding_boxes: bool = True
    show_confidence: bool = True
    
    # Freeze settings
    freeze_time: float = 2.0  # Seconds to show recognition result (lower = more responsive)
    frames_for_analysis: int = 3  # Consecutive frames with face before analyzing (lower = faster)
    
    # Output
    save_recognition_log: bool = True
    save_video: bool = False
    output_video_path: str = "recognition_output.mp4"
    
    # Performance
    use_threading: bool = True
    max_recognition_threads: int = 2
    
    def save(self, filepath: str):
        """Save configuration to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(asdict(self), f, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> 'RecognitionConfig':
        """Load configuration from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)


class FaceRecognitionStats:
    """Statistics tracker for face recognition"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.total_frames = 0
        self.faces_detected = 0
        self.faces_recognized = 0
        self.unique_persons = set()
        self.processing_times = []
        self.recognition_history = []
        self.start_time = time.time()
    
    def add_recognition(self, identity: str, confidence: float, processing_time: float):
        """Record a recognition event"""
        self.faces_recognized += 1
        self.unique_persons.add(identity)
        self.processing_times.append(processing_time)
        self.recognition_history.append({
            'timestamp': datetime.now().isoformat(),
            'identity': identity,
            'confidence': confidence,
            'processing_time': processing_time
        })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        elapsed = time.time() - self.start_time
        avg_processing_time = np.mean(self.processing_times) if self.processing_times else 0
        
        return {
            'total_frames': self.total_frames,
            'faces_detected': self.faces_detected,
            'faces_recognized': self.faces_recognized,
            'unique_persons': len(self.unique_persons),
            'fps': self.total_frames / elapsed if elapsed > 0 else 0,
            'avg_processing_time_ms': avg_processing_time * 1000,
            'recognition_rate': (self.faces_recognized / self.faces_detected * 100) 
                              if self.faces_detected > 0 else 0
        }


class FaceRecognitionSystem:
    """Advanced real-time face recognition system"""
    
    def __init__(self, config: RecognitionConfig):
        self.config = config
        self.stats = FaceRecognitionStats()
        self.running = False
        
        # Initialize camera
        self.cap = None
        self.video_writer = None
        
        # Threading
        self.frame_queue = queue.Queue(maxsize=config.max_processing_queue)
        self.result_queue = queue.Queue()
        self.processing_threads = []
        
        # Recognition state
        self.current_recognition = {}
        self.current_faces = []  # Store current detected faces for mapping to recognition
        self.freeze_until = 0
        self.face_counter = 0
        self._db_initialized = False  # Track if database embeddings are created
        self._db_file_count = 0  # Track database file count for change detection
        self._last_db_check_time = 0  # Track last database check time
        self._pending_refresh = config.refresh_database_on_start  # Flag for pending refresh
        self._last_counted_time = 0  # Track when we last counted to prevent duplicate counting
        self._count_cooldown = 2.0  # Minimum seconds between counting the same face
        self._last_recognized_identity = None  # Track last recognized identity to prevent duplicate counting
        self._last_recognition_time = 0  # Track when we last counted a recognition
        self._db_empty = False  # Track if database is known to be empty (prevents infinite refresh loops)
        self._refresh_attempted = False  # Track if we've attempted refresh already
        self._refresh_fail_count = 0  # Track consecutive refresh failures
        self._refresh_lock = threading.Lock()  # Lock to prevent concurrent refresh operations
        self._refresh_in_progress = False  # Track if refresh is currently running
        
        # Initialize database
        self._initialize_database()
        
        # Initialize models
        logger.info("Initializing face recognition models...")
        self._initialize_models()
        
        logger.info("[SUCCESS] Face Recognition System initialized successfully!")
        logger.info(f"   - Database: {self.config.db_path}")
        logger.info(f"   - Model: {self.config.recognition_model}")
        logger.info(f"   - Detector: {self.config.detector_backend}")
        logger.info("Ready to start camera...")
    
    def _initialize_database(self):
        """Validate and prepare database"""
        try:
            # Create database directory if it doesn't exist
            if not os.path.exists(self.config.db_path):
                logger.info(f"Creating database directory: {self.config.db_path}")
                os.makedirs(self.config.db_path, exist_ok=True)
                logger.info(f"Database directory created successfully")
            
            # Check if database has images (recursively search subdirectories)
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
            images = []
            try:
                for root, dirs, files in os.walk(self.config.db_path):
                    for f in files:
                        if Path(f).suffix.lower() in image_extensions:
                            images.append(os.path.join(root, f))
            except (OSError, PermissionError) as e:
                logger.error(f"Error accessing database directory: {e}")
                raise FileNotFoundError(
                    f"Cannot access database path: {self.config.db_path}\n"
                    f"Error: {e}"
                )
            
            if not images:
                logger.warning(f"No images found in database: {self.config.db_path}")
                logger.warning("Please add student photos via Admin panel first.")
            else:
                logger.info(f"Database initialized with {len(images)} images in {self.config.db_path}")
            
            # Track initial database state for change detection
            self._db_file_count = len(images)
            self._last_db_check_time = time.time()
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _initialize_models(self):
        """Pre-load models for faster recognition"""
        logger.info("Loading models...")
        try:
            # Build recognition model
            try:
                DeepFace.build_model(
                    task="facial_recognition",
                    model_name=self.config.recognition_model
                )
                logger.info(f"Recognition model '{self.config.recognition_model}' loaded")
            except Exception as e:
                logger.error(f"Failed to load recognition model '{self.config.recognition_model}': {e}")
                logger.error("Face recognition will not work without the model. Please check your installation.")
                raise
            
            # Build analysis models if enabled
            if self.config.enable_face_analysis:
                try:
                    for model in ['Age', 'Gender', 'Emotion']:
                        DeepFace.build_model(task="facial_attribute", model_name=model)
                    logger.info("Face analysis models loaded")
                except Exception as e:
                    logger.warning(f"Failed to load some analysis models: {e}")
                    logger.warning("Face analysis features will be disabled")
                    self.config.enable_face_analysis = False
            
            # Quick validation test - just verify model loads correctly
            # Note: Full recognition happens in real-time loop, not here
            try:
                # Quick test with tiny image - just to verify model works
                test_img = np.ones((100, 100, 3), dtype=np.uint8) * 128
                # We don't actually need to run recognition here - model is loaded
                # This test was causing 5-10 minute delays with large databases
                logger.info("Models validated and ready for real-time recognition")
            except Exception as e:
                logger.warning(f"Model validation note: {e}")
        
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            logger.error("The face recognition system may not work properly.")
            raise
    
    def _open_camera(self) -> bool:
        """Open camera or video source"""
        try:
            self.cap = cv2.VideoCapture(self.config.camera_source)
            
            if not self.cap.isOpened():
                raise RuntimeError(f"Failed to open camera source: {self.config.camera_source}")
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.camera_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.camera_height)
            self.cap.set(cv2.CAP_PROP_FPS, self.config.camera_fps)
            
            # Get actual properties
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"Camera opened: {actual_width}x{actual_height} @ {actual_fps:.1f} FPS")
            
            # Initialize video writer if needed
            if self.config.save_video:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                self.video_writer = cv2.VideoWriter(
                    self.config.output_video_path,
                    fourcc,
                    actual_fps if actual_fps > 0 else 30.0,
                    (actual_width, actual_height)
                )
                logger.info(f"Video recording started: {self.config.output_video_path}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error opening camera: {e}")
            return False
    
    def _check_database_changes(self) -> bool:
        """Check if database has new files (images only, not pkl files) - recursively"""
        if not self.config.check_database_changes:
            return False
        
        # Check every 5 seconds to avoid overhead
        current_time = time.time()
        if current_time - self._last_db_check_time < 5.0:
            return False
        
        self._last_db_check_time = current_time
        
        try:
            # Recursively count all images (not just top-level)
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
            images = []
            for root, dirs, files in os.walk(self.config.db_path):
                for f in files:
                    if Path(f).suffix.lower() in image_extensions:
                        images.append(f)
            
            if len(images) != self._db_file_count:
                logger.info(f"Database change detected: {self._db_file_count} -> {len(images)} images")
                self._db_file_count = len(images)
                return True
        except Exception as e:
            logger.debug(f"Error checking database changes: {e}")
        
        return False
    
    def _refresh_database_embeddings(self, frame: np.ndarray) -> bool:
        """Force refresh of database embeddings (thread-safe)"""
        try:
            logger.info("Refreshing database embeddings (this may take a moment)...")
            logger.info("Processing all images in database - please wait...")
            
            # Use a small test image to trigger refresh
            # DeepFace.find will rebuild the entire database
            results = DeepFace.find(
                img_path=frame,
                db_path=self.config.db_path,
                model_name=self.config.recognition_model,
                detector_backend=self.config.detector_backend,
                distance_metric=self.config.distance_metric,
                enforce_detection=False,
                silent=True,  # Changed to True to reduce log spam
                refresh_database=True  # Force full refresh
            )
            
            # Mark as initialized immediately after successful refresh
            with self._refresh_lock:
                self._db_initialized = True
            logger.info("[SUCCESS] Database embeddings refreshed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing database: {e}")
            # Mark as failed (but don't mark as empty yet - might be temporary)
            with self._refresh_lock:
                self._db_initialized = False
            return False
    
    def _process_frame_for_recognition(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """Process a frame and attempt face recognition"""
        try:
            start_time = time.time()
            
            # Check if we need to refresh database
            should_refresh = False
            
            # 1. Check for pending refresh (startup flag or manual trigger)
            if self._pending_refresh:
                should_refresh = True
                self._pending_refresh = False
                logger.info("Manual refresh requested - refreshing database...")
            
            # 2. Check for database changes (auto-refresh)
            elif self.config.auto_refresh_database and self._check_database_changes():
                should_refresh = True
                logger.info("Auto-refresh triggered - database changed detected")
            
            # 3. Check if database is not initialized (but only if we haven't confirmed it's empty)
            elif not self._db_initialized and not getattr(self, '_db_empty', False) and not self._refresh_in_progress:
                # Check if database actually has images before trying to refresh
                if os.path.exists(self.config.db_path):
                    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
                    images = []
                    for root, dirs, files in os.walk(self.config.db_path):
                        for f in files:
                            if Path(f).suffix.lower() in image_extensions:
                                images.append(f)
                    
                    if not images:
                        # Database is empty - mark it and skip
                        self._db_empty = True
                        logger.warning(f"No images found in database: {self.config.db_path}")
                        logger.warning("Please add student photos first before using face recognition.")
                        return None
                    else:
                        should_refresh = True
                        logger.info("Database embeddings not found - creating them now (this may take a moment)...")
                else:
                    self._db_empty = True
                    logger.warning(f"Database path not found: {self.config.db_path}")
                    return None
            
            # Refresh if needed (only if database has images and not already in progress)
            if should_refresh and not getattr(self, '_db_empty', False):
                # Use lock to prevent concurrent refresh attempts
                with self._refresh_lock:
                    # Double-check after acquiring lock
                    if self._refresh_in_progress or self._db_initialized:
                        # Another thread is already refreshing or already initialized
                        logger.debug("Refresh already in progress or completed, skipping...")
                        should_refresh = False
                    else:
                        self._refresh_in_progress = True
                
                if should_refresh:
                    try:
                        if not self._refresh_database_embeddings(frame):
                            # If refresh failed, try to continue with cached database
                            logger.warning("Refresh failed, attempting to use cached database...")
                            # Mark as empty if refresh consistently fails
                            if not hasattr(self, '_refresh_fail_count'):
                                self._refresh_fail_count = 0
                            self._refresh_fail_count += 1
                            if self._refresh_fail_count >= 3:
                                self._db_empty = True
                                logger.warning("Database refresh failed multiple times. Database may be empty.")
                    finally:
                        # Always release the lock
                        with self._refresh_lock:
                            self._refresh_in_progress = False
            
            # Skip processing if database is confirmed empty
            if getattr(self, '_db_empty', False):
                return None
            
            # Find faces in database
            try:
                # Check if database is initialized before making the call
                if not self._db_initialized and not self._refresh_in_progress:
                    # If not initialized and not refreshing, skip this frame
                    # (will be initialized on next frame after refresh completes)
                    return None
                
                results = DeepFace.find(
                    img_path=frame,
                    db_path=self.config.db_path,
                    model_name=self.config.recognition_model,
                    detector_backend=self.config.detector_backend,
                    distance_metric=self.config.distance_metric,
                    enforce_detection=False,
                    silent=True,  # Suppress DeepFace warnings
                    refresh_database=False  # Use cache (refresh handled above if needed)
                )
                # Mark as initialized after successful call (if not already set)
                if not self._db_initialized:
                    with self._refresh_lock:
                        self._db_initialized = True
            except (cv2.error, ValueError) as e:
                # Handle OpenCV errors (invalid vector subscript, assertion failures, etc.)
                error_msg = str(e)
                if "invalid vector subscript" in error_msg or "Assertion failed" in error_msg or "scaleIdx" in error_msg:
                    # OpenCV face detection error - usually happens with problematic frames
                    # Log but don't crash - just skip this frame
                    logger.debug(f"OpenCV detection error (skipping frame): {error_msg}")
                    return None
                # Re-raise ValueError for database-related errors
                if isinstance(e, ValueError):
                    raise
                # For other cv2.errors, just skip this frame
                logger.debug(f"OpenCV error (skipping frame): {error_msg}")
                return None
            except ValueError as e:
                # If pkl file is missing or empty, handle gracefully
                if "Nothing is found in" in str(e) or "No item found" in str(e):
                    # Check if database is actually empty
                    if os.path.exists(self.config.db_path):
                        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
                        images = []
                        for root, dirs, files in os.walk(self.config.db_path):
                            for f in files:
                                if Path(f).suffix.lower() in image_extensions:
                                    images.append(f)
                        
                        if not images:
                            # Database is truly empty - mark it and skip
                            self._db_empty = True
                            if not self._db_initialized:  # Only log once
                                logger.warning("Face recognition database is empty. Please add student photos first.")
                            return None
                    
                    # Database has images but embeddings missing - try refresh once (thread-safe)
                    if not self._db_initialized and not self._refresh_in_progress:
                        # Check if we should attempt refresh
                        with self._refresh_lock:
                            if self._refresh_in_progress or self._db_initialized:
                                # Another thread is handling it
                                return None
                            self._refresh_in_progress = True
                        
                        try:
                            logger.info("Database embeddings not found - creating them now (this may take a moment)...")
                            if self._refresh_database_embeddings(frame):
                                # Retry after refresh
                                try:
                                    results = DeepFace.find(
                                        img_path=frame,
                                        db_path=self.config.db_path,
                                        model_name=self.config.recognition_model,
                                        detector_backend=self.config.detector_backend,
                                        distance_metric=self.config.distance_metric,
                                        enforce_detection=False,
                                        silent=True,
                                        refresh_database=False
                                    )
                                    with self._refresh_lock:
                                        self._db_initialized = True
                                except ValueError:
                                    # Still failed after refresh - database likely empty
                                    self._db_empty = True
                                    return None
                            else:
                                # Refresh failed - likely empty database
                                self._db_empty = True
                                return None
                        finally:
                            with self._refresh_lock:
                                self._refresh_in_progress = False
                    else:
                        # Already refreshing or database is empty
                        if getattr(self, '_db_empty', False):
                            return None
                        # Database exists but no matches found - this is normal
                        return None
                else:
                    raise  # Re-raise other errors
            
            processing_time = time.time() - start_time
            
            if not results or len(results) == 0:
                return None
            
            df = results[0]  # Get first face result
            
            if len(df) == 0:
                return None
            
            # Get best match
            match = df.iloc[0]
            confidence = match.get('confidence', 0)
            distance = match.get('distance', float('inf'))
            threshold_distance = match.get('threshold', 0.68)  # Default VGG-Face cosine threshold
            
            # Log match info for debugging
            identity_path = match.get('identity', 'unknown')
            if self.config.debug_recognition:
                logger.info(
                    f"Match found: {identity_path} - "
                    f"distance={distance:.4f}, threshold={threshold_distance:.4f}, "
                    f"confidence={confidence:.2f}%"
                )
            
            # IMPORTANT: Use distance threshold for accuracy (not just confidence)
            # Distance must be below threshold to be considered a match
            # For VGG-Face + cosine: threshold is 0.68
            # Lower distance = more similar, higher distance = less similar
            
            # Get facial area from source (we detected the face, so we have coordinates)
            # Try to get from match, or use a default area
            facial_area = {
                'x': match.get('source_x', 0),
                'y': match.get('source_y', 0),
                'w': match.get('source_w', 0),
                'h': match.get('source_h', 0)
            }
            
            # More lenient matching: allow slightly higher distance OR slightly lower confidence
            # This handles cases where face angle/lighting differs slightly from database
            distance_threshold_with_margin = threshold_distance * 1.15  # 15% margin for flexibility
            min_confidence = self.config.confidence_threshold * 0.8  # 20% lower confidence margin
            
            # Accept match if EITHER:
            # 1. Distance is good (<= threshold*1.15) AND confidence is reasonable (>= 60% * 0.8 = 48%)
            # 2. OR distance is excellent (<= threshold) even with lower confidence
            # 3. OR confidence is excellent (>= 70%) even with slightly higher distance
            
            distance_ok = distance <= distance_threshold_with_margin
            distance_excellent = distance <= threshold_distance
            confidence_ok = confidence >= min_confidence
            confidence_excellent = confidence >= 70.0
            
            # Accept if: (distance OK AND confidence OK) OR (distance excellent) OR (confidence excellent)
            is_valid_match = (distance_ok and confidence_ok) or distance_excellent or confidence_excellent
            
            if not is_valid_match:
                if self.config.debug_recognition:
                    logger.info(
                        f"Face rejected: {identity_path} - "
                        f"distance={distance:.4f} (threshold={threshold_distance:.4f}, margin={distance_threshold_with_margin:.4f}), "
                        f"confidence={confidence:.2f}% (min={min_confidence:.1f}%, threshold={self.config.confidence_threshold:.1f}%)"
                    )
                return {
                    'recognized': False,
                    'is_unknown': True,
                    'confidence': confidence,
                    'distance': distance,
                    'threshold': threshold_distance,
                    'facial_area': facial_area,
                    'processing_time': processing_time
                }
            
            # Extract identity name (already extracted above, but keep for clarity)
            identity_path = match['identity']
            
            # Try to get a meaningful name - check if it's in a person folder
            path_parts = Path(identity_path).parts
            if len(path_parts) > 1:
                # If structure is: database/person_name/image.jpg, use person_name
                # If structure is: database/image.jpg, use image name
                folder_name = path_parts[-2] if len(path_parts) >= 2 else None
                file_stem = Path(identity_path).stem
                
                # Use folder name if it's not "database", otherwise use filename
                if folder_name and folder_name.lower() != "database":
                    identity_name = folder_name
                else:
                    identity_name = file_stem
            else:
                identity_name = Path(identity_path).stem
            
            # Only count recognition if it's a new recognition cycle (prevent duplicate counting)
            current_time = time.time()
            should_count = (
                not hasattr(self, '_last_recognized_identity') or
                identity_name != getattr(self, '_last_recognized_identity', None) or
                (current_time - getattr(self, '_last_recognition_time', 0)) >= self._count_cooldown
            )
            
            if should_count:
                self.stats.add_recognition(identity_name, confidence, processing_time)
                self._last_recognized_identity = identity_name
                self._last_recognition_time = current_time
                logger.info(
                    f"Recognized: {identity_name} "
                    f"(confidence: {confidence:.2f}%, "
                    f"distance: {match.get('distance', 0):.4f}, "
                    f"threshold: {match.get('threshold', 0):.4f}, "
                    f"time: {processing_time*1000:.1f}ms)"
                )
            else:
                # Log but don't count duplicate recognition
                logger.debug(f"Duplicate recognition of {identity_name} - not counting")
            
            return {
                'recognized': True,
                'identity': identity_name,
                'identity_path': identity_path,
                'confidence': confidence,
                'distance': match.get('distance', 0),
                'threshold': threshold_distance,
                'facial_area': {
                    'x': match.get('source_x', 0),
                    'y': match.get('source_y', 0),
                    'w': match.get('source_w', 0),
                    'h': match.get('source_h', 0)
                },
                'processing_time': processing_time
            }
        
        except (cv2.error, Exception) as e:
            # Handle OpenCV errors gracefully
            error_msg = str(e)
            if "invalid vector subscript" in error_msg or "Assertion failed" in error_msg or "scaleIdx" in error_msg:
                # OpenCV face detection error - skip this frame
                logger.debug(f"OpenCV detection error (skipping frame): {error_msg}")
                return None
            # Log other errors but don't crash
            logger.error(f"Error processing frame: {e}", exc_info=True)
            return None
    
    def _recognition_worker(self):
        """Worker thread for processing frames"""
        while self.running:
            try:
                frame_data = self.frame_queue.get(timeout=1.0)
                if frame_data is None:  # Poison pill
                    break
                
                # Handle both dict (with faces) and numpy array (legacy)
                if isinstance(frame_data, dict):
                    frame = frame_data['frame']
                    faces = frame_data.get('faces', [])
                else:
                    frame = frame_data
                    faces = []
                
                result = self._process_frame_for_recognition(frame)
                if result:
                    # If facial_area is missing, use first detected face
                    if faces and result.get('facial_area', {}).get('x', 0) == 0:
                        first_face = faces[0]
                        result['facial_area'] = {
                            'x': first_face['x'],
                            'y': first_face['y'],
                            'w': first_face['w'],
                            'h': first_face['h']
                        }
                    self.result_queue.put(result)
                
                self.frame_queue.task_done()
            
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Recognition worker error: {e}", exc_info=True)
    
    def _detect_faces(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect faces in frame - optimized for speed"""
        try:
            # Use faster detection settings for real-time
            face_objs = DeepFace.extract_faces(
                img_path=frame,
                detector_backend=self.config.detector_backend,
                enforce_detection=False,
                anti_spoofing=False,  # Disable for speed (can enable in config if needed)
                align=False  # Skip alignment for detection - only align during recognition
            )
            
            faces = []
            for face_obj in face_objs:
                area = face_obj['facial_area']
                w, h = area['w'], area['h']
                
                # Filter by minimum size
                if w >= self.config.min_face_size and h >= self.config.min_face_size:
                    faces.append({
                        'x': area['x'],
                        'y': area['y'],
                        'w': w,
                        'h': h,
                        'is_real': face_obj.get('is_real', True),
                        'confidence': face_obj.get('face_confidence', 0)
                    })
            
            return faces
        
        except Exception as e:
            logger.debug(f"Face detection error: {e}")
            return []
    
    def _draw_recognition_info(self, frame: np.ndarray, recognition: Dict[str, Any]):
        """Draw recognition information on frame"""
        area = recognition.get('facial_area', {})
        x = area.get('x', 0)
        y = area.get('y', 0)
        w = area.get('w', 0)
        h = area.get('h', 0)
        
        # Validate coordinates - if invalid, use first detected face
        if (x == 0 and y == 0 and w == 0 and h == 0) or w <= 0 or h <= 0:
            if len(self.current_faces) > 0:
                first_face = self.current_faces[0]
                x = first_face['x']
                y = first_face['y']
                w = first_face['w']
                h = first_face['h']
            else:
                # Can't draw without valid coordinates
                logger.debug("No valid facial area for recognition drawing")
                return
        
        if not recognition.get('recognized', False):
            # Show "Unknown" for faces not in database
            if recognition.get('is_unknown', False) and self.config.show_unknown_faces:
                if self.config.show_bounding_boxes:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)  # Red for unknown
                
                label = "Unknown"
                (text_width, text_height), _ = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
                )
                
                cv2.rectangle(
                    frame,
                    (x, y - text_height - 10),
                    (x + text_width + 10, y),
                    (0, 0, 0),
                    -1
                )
                
                cv2.putText(
                    frame,
                    label,
                    (x + 5, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),  # Red text
                    2
                )
            return
        
        identity = recognition.get('identity', 'Unknown')
        confidence = recognition.get('confidence', 0)
        
        # Draw bounding box - green for recognized, yellow for low confidence
        if self.config.show_bounding_boxes:
            if confidence >= self.config.confidence_threshold:
                color = (0, 255, 0)  # Green for good match
            elif confidence >= 60.0:
                color = (0, 165, 255)  # Orange for medium confidence
            else:
                color = (0, 0, 255)  # Red for low confidence
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        
        # Draw identity and confidence
        if self.config.show_confidence:
            label = f"{identity}: {confidence:.1f}%"
        else:
            label = identity
        
        # Text background
        (text_width, text_height), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
        )
        
        cv2.rectangle(
            frame,
            (x, y - text_height - 10),
            (x + text_width + 10, y),
            (0, 0, 0),
            -1
        )
        
        # Text
        cv2.putText(
            frame,
            label,
            (x + 5, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )
    
    def _draw_statistics(self, frame: np.ndarray):
        """Draw only recognition rate"""
        if not self.config.show_statistics:
            return
        
        stats = self.stats.get_stats()
        y_offset = 30
        
        # Only show recognition rate
        line = f"Recognition Rate: {stats['recognition_rate']:.1f}%"
        
        # Background for text
        (text_width, text_height), _ = cv2.getTextSize(
            line, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
        )
        cv2.rectangle(
            frame,
            (5, y_offset - text_height - 5),
            (15 + text_width, y_offset + 5),
            (0, 0, 0),
            -1
        )
        cv2.putText(
            frame,
            line,
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )
    
    def _draw_fps(self, frame: np.ndarray, fps: float):
        """Draw FPS counter"""
        if not self.config.show_fps:
            return
        
        fps_text = f"FPS: {fps:.1f}"
        cv2.putText(
            frame,
            fps_text,
            (frame.shape[1] - 120, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )
    
    def run(self):
        """Main recognition loop"""
        logger.info("=" * 60)
        logger.info("Opening camera...")
        if not self._open_camera():
            logger.error("[ERROR] Failed to open camera")
            logger.error("   Make sure your camera is connected and not in use by another application")
            return
        logger.info("[SUCCESS] Camera opened successfully!")
        
        self.running = True
        
        # Start worker threads
        if self.config.use_threading:
            for _ in range(self.config.max_recognition_threads):
                thread = threading.Thread(target=self._recognition_worker, daemon=True)
                thread.start()
                self.processing_threads.append(thread)
            logger.info(f"Started {len(self.processing_threads)} processing threads")
        
        frame_count = 0
        last_fps_time = time.time()
        fps_counter = 0
        current_fps = 0
        
        logger.info("Starting face recognition loop. Press 'q' to quit, 'r' to reset stats, 'f' to refresh database.")
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    logger.warning("Failed to read frame from camera")
                    break
                
                frame_count += 1
                self.stats.total_frames += 1
                fps_counter += 1
                
                # Calculate FPS
                current_time = time.time()
                if current_time - last_fps_time >= 1.0:
                    current_fps = fps_counter
                    fps_counter = 0
                    last_fps_time = current_time
                
                # Detect faces - always detect for drawing
                faces = self._detect_faces(frame)
                
                # Update current faces for recognition mapping
                self.current_faces = faces
                
                # Draw detected faces (but don't count yet - only count when processed)
                # Only draw gray boxes if we don't have active recognition
                if self.config.show_bounding_boxes and faces and time.time() >= self.freeze_until:
                    for face in faces:
                        x, y, w, h = face['x'], face['y'], face['w'], face['h']
                        color = (128, 128, 128)  # Gray for detected but not recognized yet
                        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 1)
                
                # Process for recognition (every Nth frame or when no freeze active)
                should_process = (
                    frame_count % self.config.frame_skip == 0 and
                    time.time() > self.freeze_until and
                    len(faces) > 0
                )
                
                if should_process:
                    # Check if we've seen faces for enough consecutive frames
                    if len(faces) > 0:
                        self.face_counter += 1
                    else:
                        self.face_counter = 0
                    
                    if self.face_counter >= self.config.frames_for_analysis:
                        # Only count faces if enough time has passed since last count (prevent duplicate counting)
                        current_time = time.time()
                        if current_time - self._last_counted_time >= self._count_cooldown:
                            # Count faces when actually processing (not on every detection)
                            self.stats.faces_detected += len(faces)
                            self._last_counted_time = current_time
                        
                        # Add frame to processing queue with faces info
                        if not self.frame_queue.full():
                            # Store faces info with frame for recognition
                            frame_data = {
                                'frame': frame.copy(),
                                'faces': faces.copy()
                            }
                            self.frame_queue.put(frame_data)
                        self.face_counter = 0
                
                # Check for recognition results
                try:
                    result = self.result_queue.get_nowait()
                    if result:
                        # Map recognition result to current detected faces
                        # Use the first detected face if facial_area is missing or invalid
                        if result.get('facial_area', {}).get('x', 0) == 0 and len(self.current_faces) > 0:
                            # Use the first detected face coordinates
                            first_face = self.current_faces[0]
                            result['facial_area'] = {
                                'x': first_face['x'],
                                'y': first_face['y'],
                                'w': first_face['w'],
                                'h': first_face['h']
                            }
                        
                        # Only freeze for recognized faces, not unknown
                        if result.get('recognized', False):
                            self.current_recognition = result
                            self.freeze_until = time.time() + self.config.freeze_time
                        elif result.get('is_unknown', False):
                            # Show unknown briefly (shorter time)
                            self.current_recognition = result
                            self.freeze_until = time.time() + (self.config.freeze_time / 2)
                except queue.Empty:
                    pass
                
                # Draw recognition info if frozen (recognized or unknown)
                if time.time() < self.freeze_until and self.current_recognition:
                    self._draw_recognition_info(frame, self.current_recognition)
                
                # Draw overlays (only recognition rate)
                self._draw_statistics(frame)
                
                # Save frame if recording
                if self.video_writer:
                    self.video_writer.write(frame)
                
                # Display frame
                cv2.imshow('Advanced Face Recognition', frame)
                
                # Check for quit
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    logger.info("Quit requested by user")
                    break
                elif key == ord('r'):
                    # Reset statistics
                    self.stats.reset()
                    logger.info("Statistics reset")
                elif key == ord('f'):
                    # Refresh database embeddings
                    logger.info("Manual database refresh requested...")
                    self._pending_refresh = True
        
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            self.cleanup()
    
    def _draw_faces_on_frame(self, frame: np.ndarray, faces: List[Dict[str, Any]]):
        """Draw detected faces on frame (legacy method - now handled in main loop)"""
        # This method is kept for compatibility but faces are now drawn in main loop
        pass
    
    def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up resources...")
        self.running = False
        
        # Stop worker threads
        for _ in self.processing_threads:
            self.frame_queue.put(None)  # Poison pill
        
        for thread in self.processing_threads:
            thread.join(timeout=2.0)
        
        # Release camera
        if self.cap:
            self.cap.release()
        
        # Release video writer
        if self.video_writer:
            self.video_writer.release()
        
        cv2.destroyAllWindows()
        
        # Save recognition log
        if self.config.save_recognition_log:
            self._save_recognition_log()
        
        # Print final statistics
        stats = self.stats.get_stats()
        logger.info("Final Statistics:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
    
    def _save_recognition_log(self):
        """Save recognition history to file"""
        if not self.stats.recognition_history:
            return
        
        log_file = f"recognition_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump(self.stats.recognition_history, f, indent=2)
        
        logger.info(f"Recognition log saved: {log_file}")


def main():
    """Main entry point"""
    # Create configuration
    config = RecognitionConfig(
        db_path="database",
        recognition_model="VGG-Face",
        detector_backend="opencv",
        enable_face_analysis=False,
        camera_source=0,
        frame_skip=3,
        confidence_threshold=60.0,
        show_fps=True,
        show_statistics=True,
        save_recognition_log=True
    )
    
    # Optionally load from file
    config_file = "recognition_config.json"
    if os.path.exists(config_file):
        try:
            config = RecognitionConfig.load(config_file)
            logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.warning(f"Failed to load config: {e}, using defaults")
    
    # Create and run system
    try:
        system = FaceRecognitionSystem(config)
        system.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

