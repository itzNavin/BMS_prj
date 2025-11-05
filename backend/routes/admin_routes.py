"""
Admin Routes
Handles admin dashboard, student management, bus management
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from backend.models import db, User, Student, Bus, StudentBusAssignment, AuthenticationLog
from backend.services.student_service import StudentService
from backend.services.bus_service import BusService

bp = Blueprint('admin', __name__)

# Services (lazy initialization to avoid blocking on startup)
_student_service = None
_bus_service = None

def get_student_service():
    """Get or create student service instance"""
    global _student_service
    if _student_service is None:
        _student_service = StudentService()
    return _student_service

def get_bus_service():
    """Get or create bus service instance"""
    global _bus_service
    if _bus_service is None:
        _bus_service = BusService()
    return _bus_service


def admin_required(f):
    """Decorator to require admin role"""
    from functools import wraps
    
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('driver.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard"""
    if current_user.role != 'admin':
        return redirect(url_for('driver.dashboard'))
    
    # Get statistics
    total_students = Student.query.count()
    total_buses = Bus.query.count()
    total_drivers = User.query.filter_by(role='driver').count()
    
    # Get today's authentication logs
    from datetime import datetime, timedelta
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_logs = AuthenticationLog.query.filter(
        AuthenticationLog.timestamp >= today_start
    ).count()
    
    # Get recent logs
    recent_logs = AuthenticationLog.query.order_by(
        AuthenticationLog.timestamp.desc()
    ).limit(10).all()
    
    stats = {
        'total_students': total_students,
        'total_buses': total_buses,
        'total_drivers': total_drivers,
        'today_entries': today_logs
    }
    
    return render_template('admin/dashboard.html', stats=stats, recent_logs=recent_logs)


@bp.route('/students')
@admin_required
def students():
    """Student management page"""
    students_list = Student.query.order_by(Student.name).all()
    return render_template('admin/student_management.html', students=students_list)


@bp.route('/students/add', methods=['GET', 'POST'])
@admin_required
def add_student():
    """Add new student"""
    if request.method == 'POST':
        try:
            student_data = {
                'student_id': request.form.get('student_id', '').strip(),
                'name': request.form.get('name', '').strip(),
                'class_name': request.form.get('class_name', '').strip(),
                'section': request.form.get('section', '').strip()
            }
            
            # Get uploaded photos
            photos = request.files.getlist('photos')
            
            # Validate
            if not student_data['student_id'] or not student_data['name']:
                flash('Student ID and Name are required.', 'error')
                return render_template('admin/add_student.html')
            
            if not photos or len(photos) == 0 or not photos[0].filename:
                flash('Please upload at least one photo.', 'error')
                return render_template('admin/add_student.html')
            
            # Add student using service
            result = get_student_service().add_student(student_data, photos)
            
            if result['success']:
                flash(f'Student {student_data["name"]} added successfully!', 'success')
                return redirect(url_for('admin.students'))
            else:
                flash(result.get('message', 'Error adding student.'), 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('admin/add_student.html')


@bp.route('/students/<int:student_id>/delete', methods=['POST'])
@admin_required
def delete_student(student_id):
    """Delete student"""
    try:
        result = get_student_service().delete_student(student_id)
        if result['success']:
            flash('Student deleted successfully.', 'success')
        else:
            flash(result.get('message', 'Error deleting student.'), 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('admin.students'))


@bp.route('/buses')
@admin_required
def buses():
    """Bus management page"""
    buses_list = Bus.query.order_by(Bus.bus_number).all()
    drivers = User.query.filter_by(role='driver').all()
    return render_template('admin/bus_management.html', buses=buses_list, drivers=drivers)


@bp.route('/buses/add', methods=['GET', 'POST'])
@admin_required
def add_bus():
    """Add new bus"""
    if request.method == 'POST':
        try:
            bus_data = {
                'bus_number': request.form.get('bus_number', '').strip(),
                'route_name': request.form.get('route_name', '').strip(),
                'driver_id': request.form.get('driver_id') or None,
                'capacity': int(request.form.get('capacity', 50))
            }
            
            result = get_bus_service().add_bus(bus_data)
            
            if result['success']:
                flash(f'Bus {bus_data["bus_number"]} added successfully!', 'success')
                return redirect(url_for('admin.buses'))
            else:
                flash(result.get('message', 'Error adding bus.'), 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    
    drivers = User.query.filter_by(role='driver').all()
    return render_template('admin/add_bus.html', drivers=drivers)


@bp.route('/buses/<int:bus_id>/assign', methods=['GET', 'POST'])
@admin_required
def assign_students(bus_id):
    """Assign students to bus"""
    bus = Bus.query.get_or_404(bus_id)
    
    if request.method == 'POST':
        try:
            student_ids = request.form.getlist('student_ids')
            result = get_bus_service().assign_students(bus_id, student_ids)
            
            if result['success']:
                flash(f'Students assigned to bus {bus.bus_number} successfully!', 'success')
                return redirect(url_for('admin.buses'))
            else:
                flash(result.get('message', 'Error assigning students.'), 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    
    # Get all students and current assignments
    all_students = Student.query.order_by(Student.name).all()
    assigned_student_ids = [a.student_id for a in bus.student_assignments.filter_by(status='active').all()]
    
    return render_template('admin/assign_students.html', 
                         bus=bus, 
                         students=all_students,
                         assigned_student_ids=assigned_student_ids)


@bp.route('/logs')
@admin_required
def logs():
    """View authentication logs"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    logs = AuthenticationLog.query.order_by(
        AuthenticationLog.timestamp.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/logs.html', logs=logs)


@bp.route('/users')
@admin_required
def users():
    """User management page"""
    users_list = User.query.order_by(User.username).all()
    return render_template('admin/user_management.html', users=users_list)

