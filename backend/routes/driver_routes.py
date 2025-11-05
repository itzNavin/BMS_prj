"""
Driver Routes
Handles driver dashboard and face scanning
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from backend.models import db, Bus, AuthenticationLog, Student
from datetime import datetime

bp = Blueprint('driver', __name__)


@bp.route('/dashboard')
@login_required
def dashboard():
    """Driver dashboard"""
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    
    # Get driver's bus
    bus = Bus.query.filter_by(driver_id=current_user.id).first()
    
    # Get today's statistics
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_logs = AuthenticationLog.query.filter(
        AuthenticationLog.driver_id == current_user.id,
        AuthenticationLog.timestamp >= today_start
    ).all()
    
    today_granted = sum(1 for log in today_logs if log.access_granted)
    today_denied = len(today_logs) - today_granted
    
    stats = {
        'bus': bus,
        'today_total': len(today_logs),
        'today_granted': today_granted,
        'today_denied': today_denied
    }
    
    return render_template('driver/dashboard.html', stats=stats)


@bp.route('/scanning')
@login_required
def scanning():
    """Face scanning interface"""
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    
    bus = Bus.query.filter_by(driver_id=current_user.id).first()
    
    if not bus:
        flash('No bus assigned to you. Please contact administrator.', 'error')
        return redirect(url_for('driver.dashboard'))
    
    return render_template('driver/face_scanning.html', bus=bus)


@bp.route('/api/log-recognition', methods=['POST'])
@login_required
def log_recognition():
    """API endpoint to log recognition event"""
    try:
        data = request.get_json()
        
        student_id = data.get('student_id')
        bus_id = data.get('bus_id')
        confidence = data.get('confidence')
        access_granted = data.get('access_granted', False)
        reason = data.get('reason', '')
        
        log = AuthenticationLog(
            student_id=student_id,
            bus_id=bus_id,
            driver_id=current_user.id,
            recognition_confidence=confidence,
            access_granted=access_granted,
            access_denied_reason=reason if not access_granted else None
        )
        
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Recognition logged successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/entries/clear', methods=['POST'])
@login_required
def clear_entries():
    """Clear today's authentication entries for this driver"""
    try:
        from datetime import datetime
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        deleted_count = AuthenticationLog.query.filter(
            AuthenticationLog.driver_id == current_user.id,
            AuthenticationLog.timestamp >= today_start
        ).delete()
        
        db.session.commit()
        flash(f'Successfully cleared {deleted_count} entry/entries for today.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing entries: {str(e)}', 'error')
    
    return redirect(url_for('driver.dashboard'))
