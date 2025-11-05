"""
Bus Service
Business logic for bus management
"""

from backend.models import db, Bus, StudentBusAssignment
from datetime import datetime


class BusService:
    """Service for bus operations"""
    
    def add_bus(self, bus_data):
        """
        Add a new bus
        
        Args:
            bus_data: dict with bus_number, route_name, driver_id, capacity
            
        Returns:
            dict with 'success' and optional 'message'
        """
        try:
            # Check if bus_number already exists
            existing = Bus.query.filter_by(bus_number=bus_data['bus_number']).first()
            if existing:
                return {
                    'success': False,
                    'message': f'Bus number {bus_data["bus_number"]} already exists.'
                }
            
            # Validate driver_id if provided
            if bus_data.get('driver_id'):
                from backend.models import User
                driver = User.query.get(bus_data['driver_id'])
                if not driver or driver.role != 'driver':
                    return {
                        'success': False,
                        'message': 'Invalid driver selected.'
                    }
            
            # Create bus
            bus = Bus(
                bus_number=bus_data['bus_number'],
                route_name=bus_data.get('route_name'),
                driver_id=bus_data.get('driver_id'),
                capacity=bus_data.get('capacity', 50)
            )
            
            db.session.add(bus)
            db.session.commit()
            
            return {
                'success': True,
                'bus': bus,
                'message': f'Bus {bus.bus_number} added successfully!'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error adding bus: {str(e)}'
            }
    
    def assign_students(self, bus_id, student_ids):
        """
        Assign students to a bus
        
        Args:
            bus_id: Bus database ID
            student_ids: list of student database IDs
            
        Returns:
            dict with 'success' and optional 'message'
        """
        try:
            bus = Bus.query.get(bus_id)
            if not bus:
                return {
                    'success': False,
                    'message': 'Bus not found.'
                }
            
            # Deactivate all existing assignments for this bus
            existing_assignments = StudentBusAssignment.query.filter_by(
                bus_id=bus_id,
                status='active'
            ).all()
            
            for assignment in existing_assignments:
                assignment.status = 'inactive'
            
            # Create new assignments
            for student_id in student_ids:
                student_id = int(student_id)
                
                # Check if student exists
                from backend.models import Student
                student = Student.query.get(student_id)
                if not student:
                    continue
                
                # Check if assignment already exists (inactive)
                existing = StudentBusAssignment.query.filter_by(
                    student_id=student_id,
                    bus_id=bus_id
                ).first()
                
                if existing:
                    # Reactivate
                    existing.status = 'active'
                    existing.assigned_at = datetime.utcnow()
                else:
                    # Create new
                    assignment = StudentBusAssignment(
                        student_id=student_id,
                        bus_id=bus_id,
                        status='active'
                    )
                    db.session.add(assignment)
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Students assigned to bus {bus.bus_number} successfully!'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error assigning students: {str(e)}'
            }
    
    def delete_bus(self, bus_id):
        """
        Delete a bus
        
        Args:
            bus_id: Bus database ID
            
        Returns:
            dict with 'success' and optional 'message'
        """
        try:
            bus = Bus.query.get(bus_id)
            if not bus:
                return {
                    'success': False,
                    'message': 'Bus not found.'
                }
            
            bus_number = bus.bus_number
            
            # Delete bus (cascades to assignments)
            db.session.delete(bus)
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Bus {bus_number} deleted successfully.'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error deleting bus: {str(e)}'
            }

