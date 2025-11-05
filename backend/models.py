"""
Database Models for Bus Management System
SQLAlchemy ORM models
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# db will be initialized in app.py
db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for authentication (Admin and Driver)"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' or 'driver'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    driver_buses = db.relationship('Bus', backref='driver', lazy='dynamic', foreign_keys='Bus.driver_id')
    authentication_logs = db.relationship('AuthenticationLog', backref='driver_user', lazy='dynamic')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Student(db.Model):
    """Student model"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False, index=True)  # School ID
    name = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(50), nullable=True)  # 'class' is a Python keyword
    section = db.Column(db.String(10), nullable=True)
    photo_path = db.Column(db.String(255), nullable=True)  # Path to face images folder
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bus_assignments = db.relationship('StudentBusAssignment', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    authentication_logs = db.relationship('AuthenticationLog', backref='student', lazy='dynamic')
    
    def __repr__(self):
        return f'<Student {self.student_id}: {self.name}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'name': self.name,
            'class_name': self.class_name,
            'section': self.section,
            'photo_path': self.photo_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_active_bus_assignment(self):
        """Get active bus assignment"""
        return self.bus_assignments.filter_by(status='active').first()
    
    def is_assigned_to_bus(self, bus_id):
        """Check if student is assigned to a specific bus"""
        assignment = self.bus_assignments.filter_by(
            bus_id=bus_id,
            status='active'
        ).first()
        return assignment is not None


class Bus(db.Model):
    """Bus model"""
    __tablename__ = 'buses'
    
    id = db.Column(db.Integer, primary_key=True)
    bus_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    route_name = db.Column(db.String(100), nullable=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    capacity = db.Column(db.Integer, default=50)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student_assignments = db.relationship('StudentBusAssignment', backref='bus', lazy='dynamic', cascade='all, delete-orphan')
    authentication_logs = db.relationship('AuthenticationLog', backref='bus', lazy='dynamic')
    
    def __repr__(self):
        return f'<Bus {self.bus_number}: {self.route_name}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'bus_number': self.bus_number,
            'route_name': self.route_name,
            'driver_id': self.driver_id,
            'driver_name': self.driver.username if self.driver else None,
            'capacity': self.capacity,
            'current_students': self.get_student_count(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_student_count(self):
        """Get count of active students assigned to this bus"""
        return self.student_assignments.filter_by(status='active').count()
    
    def get_students(self):
        """Get all active students assigned to this bus"""
        assignments = self.student_assignments.filter_by(status='active').all()
        return [assignment.student for assignment in assignments]


class StudentBusAssignment(db.Model):
    """Student-Bus Assignment model (Many-to-Many relationship)"""
    __tablename__ = 'student_bus_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    bus_id = db.Column(db.Integer, db.ForeignKey('buses.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # 'active' or 'inactive'
    
    # Unique constraint: one student can only have one active assignment per bus
    __table_args__ = (db.UniqueConstraint('student_id', 'bus_id', name='unique_student_bus'),)
    
    def __repr__(self):
        return f'<Assignment: Student {self.student_id} -> Bus {self.bus_id} ({self.status})>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'bus_id': self.bus_id,
            'bus_number': self.bus.bus_number if self.bus else None,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'status': self.status
        }


class AuthenticationLog(db.Model):
    """Authentication Log model for tracking face recognition events"""
    __tablename__ = 'authentication_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    bus_id = db.Column(db.Integer, db.ForeignKey('buses.id'), nullable=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    recognition_confidence = db.Column(db.Float, nullable=True)
    access_granted = db.Column(db.Boolean, default=False)
    access_denied_reason = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    face_image_path = db.Column(db.String(255), nullable=True)  # Optional: save snapshot
    
    def __repr__(self):
        status = "GRANTED" if self.access_granted else "DENIED"
        return f'<AuthLog {self.id}: Student {self.student_id} - {status}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'bus_id': self.bus_id,
            'bus_number': self.bus.bus_number if self.bus else None,
            'driver_id': self.driver_id,
            'driver_name': self.driver_user.username if self.driver_user else None,
            'recognition_confidence': self.recognition_confidence,
            'access_granted': self.access_granted,
            'access_denied_reason': self.access_denied_reason,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'face_image_path': self.face_image_path
        }

