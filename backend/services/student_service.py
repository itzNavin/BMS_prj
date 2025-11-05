"""
Student Service
Business logic for student management
"""

import logging
from backend.models import db, Student
from utils import save_student_photos, copy_photos_to_face_db
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class StudentService:
    """Service for student operations"""
    
    def __init__(self):
        # Lazy initialization - don't create service until needed
        self._face_recognition_service = None
    
    @property
    def face_recognition_service(self):
        """Lazy initialization of face recognition service"""
        if self._face_recognition_service is None:
            # Import only when needed to avoid blocking at startup
            from utils import BusFaceRecognitionService
            self._face_recognition_service = BusFaceRecognitionService()
        return self._face_recognition_service
    
    def add_student(self, student_data, photos):
        """
        Add a new student with photos
        
        Args:
            student_data: dict with student_id, name, class_name, section
            photos: list of uploaded photo files
            
        Returns:
            dict with 'success' and optional 'message'
        """
        try:
            # Check if student_id already exists
            existing = Student.query.filter_by(student_id=student_data['student_id']).first()
            if existing:
                return {
                    'success': False,
                    'message': f'Student ID {student_data["student_id"]} already exists.'
                }
            
            # Create student record
            student = Student(
                student_id=student_data['student_id'],
                name=student_data['name'],
                class_name=student_data.get('class_name'),
                section=student_data.get('section')
            )
            db.session.add(student)
            db.session.flush()  # Get student.id without committing
            
            # Save photos to uploads directory
            saved_paths = save_student_photos(photos, student.id)
            
            if not saved_paths:
                db.session.rollback()
                return {
                    'success': False,
                    'message': 'Failed to save photos. Please try again.'
                }
            
            # Set photo_path
            student.photo_path = f"uploads/students/{student.id}/"
            
            # Copy photos to face recognition database (use absolute path from config)
            from config import FACE_RECOGNITION_DB
            face_db_base = str(FACE_RECOGNITION_DB)
            face_db_paths = copy_photos_to_face_db(saved_paths, student.name, face_db_base)
            
            if not face_db_paths:
                # Warning but don't fail - photos are saved in uploads
                logger.warning(f"Failed to copy photos to face recognition DB for {student.name}")
            
            # Trigger face recognition database refresh
            try:
                self.face_recognition_service.add_student_photos(saved_paths, student.name)
                self.face_recognition_service.trigger_database_refresh()
            except Exception as e:
                logger.warning(f"Face recognition refresh failed: {e}")
                # Don't fail the operation - can refresh manually later
            
            # Commit transaction
            db.session.commit()
            
            return {
                'success': True,
                'student': student,
                'message': f'Student {student.name} added successfully!'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error adding student: {str(e)}'
            }
    
    def delete_student(self, student_id):
        """
        Delete a student and all associated data
        
        Args:
            student_id: Student database ID
            
        Returns:
            dict with 'success' and optional 'message'
        """
        try:
            student = Student.query.get(student_id)
            if not student:
                return {
                    'success': False,
                    'message': 'Student not found.'
                }
            
            student_name = student.name
            
            # Delete photos from uploads
            from utils import delete_student_photos
            delete_student_photos(student.id)
            
            # Delete from face recognition database
            from utils import delete_student_from_face_db
            delete_student_from_face_db(student_name)
            
            # Delete student record (cascades to assignments and logs)
            db.session.delete(student)
            db.session.commit()
            
            # Trigger refresh
            try:
                self.face_recognition_service.trigger_database_refresh()
            except:
                pass  # Non-critical
            
            return {
                'success': True,
                'message': f'Student {student_name} deleted successfully.'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error deleting student: {str(e)}'
            }
    
    def update_student(self, student_id, student_data):
        """
        Update student information
        
        Args:
            student_id: Student database ID
            student_data: dict with updated fields
            
        Returns:
            dict with 'success' and optional 'message'
        """
        try:
            student = Student.query.get(student_id)
            if not student:
                return {
                    'success': False,
                    'message': 'Student not found.'
                }
            
            # Update fields
            if 'name' in student_data:
                student.name = student_data['name']
            if 'class_name' in student_data:
                student.class_name = student_data['class_name']
            if 'section' in student_data:
                student.section = student_data['section']
            
            db.session.commit()
            
            return {
                'success': True,
                'student': student,
                'message': 'Student updated successfully.'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error updating student: {str(e)}'
            }

