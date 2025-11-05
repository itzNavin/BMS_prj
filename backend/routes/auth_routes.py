"""
Authentication Routes
Handles login, logout, and user registration
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from backend.models import db, User

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication"""
    if current_user.is_authenticated:
        # Redirect based on role
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('driver.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        # Validation
        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('auth/login.html')
        
        # Find user
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Login successful
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Redirect based on role
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('driver.dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    username = current_user.username
    logout_user()
    flash(f'You have been logged out, {username}.', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Register new user (Admin only)"""
    # Only admins can register new users
    if current_user.role != 'admin':
        flash('Access denied. Only administrators can register users.', 'error')
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'driver')  # Default to driver
        
        # Validation
        if not username or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('auth/register.html')
        
        if role not in ['admin', 'driver']:
            flash('Invalid role. Must be admin or driver.', 'error')
            return render_template('auth/register.html')
        
        # Check if username exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose another.', 'error')
            return render_template('auth/register.html')
        
        # Create new user
        try:
            new_user = User(
                username=username,
                role=role
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            
            flash(f'User {username} registered successfully as {role}.', 'success')
            return redirect(url_for('admin.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error registering user: {str(e)}', 'error')
    
    return render_template('auth/register.html')

