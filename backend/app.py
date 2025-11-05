"""
Main Flask Application
Bus Management System with Face Recognition
"""

from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager
from flask_socketio import SocketIO, emit
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import configuration
try:
    import config
except ImportError:
    print("Error: config.py not found. Please create it from the template.")
    sys.exit(1)

# Initialize Flask app
app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

# Load configuration
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['DEBUG'] = config.DEBUG
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS
app.config['UPLOAD_FOLDER'] = str(config.UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = config.MAX_UPLOAD_SIZE

# Configure database engine options for connection pooling
if hasattr(config, 'SQLALCHEMY_ENGINE_OPTIONS'):
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = config.SQLALCHEMY_ENGINE_OPTIONS

# Initialize extensions
from backend.models import db
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Initialize SocketIO for real-time communication
# Using 'threading' mode for Python 3.13 compatibility (eventlet has ssl issues)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Import models (must be after db initialization)
from backend.models import User, Student, Bus, StudentBusAssignment, AuthenticationLog

# Import routes
from backend.routes import auth_routes, admin_routes, driver_routes

# Register blueprints
app.register_blueprint(auth_routes.bp, url_prefix='/auth')
app.register_blueprint(admin_routes.bp, url_prefix='/admin')
app.register_blueprint(driver_routes.bp, url_prefix='/driver')

# Import face recognition service for SocketIO (lazy import - only when needed)
# from backend.services.face_recognition_service import get_recognition_service


# SocketIO Event Handlers for Real-time Face Recognition
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to server'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    try:
        from backend.services.face_recognition_service import get_recognition_service
        recognition_service = get_recognition_service()
        recognition_service.stop_recognition(request.sid)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.debug(f"Error stopping recognition on disconnect: {e}")
    print(f"Client disconnected: {request.sid}")


@socketio.on('start_recognition')
def handle_start_recognition(data):
    """Handle start recognition request"""
    try:
        from flask_login import current_user
        from backend.services.face_recognition_service import get_recognition_service
        
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        if current_user.role != 'driver':
            emit('error', {'message': 'Only drivers can start recognition'})
            return
        
        bus_id = data.get('bus_id')
        if not bus_id:
            # Get driver's bus
            from backend.models import Bus
            bus = Bus.query.filter_by(driver_id=current_user.id).first()
            if not bus:
                emit('error', {'message': 'No bus assigned to you'})
                return
            bus_id = bus.id
        
        recognition_service = get_recognition_service()
        success = recognition_service.start_recognition(
            session_id=request.sid,
            bus_id=bus_id,
            driver_id=current_user.id
        )
        
        if success:
            emit('recognition_started', {'message': 'Recognition started', 'bus_id': bus_id})
        else:
            emit('error', {'message': 'Failed to start recognition'})
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error in start_recognition: {e}")
        emit('error', {'message': 'Internal server error'})


@socketio.on('stop_recognition')
def handle_stop_recognition():
    """Handle stop recognition request"""
    try:
        from backend.services.face_recognition_service import get_recognition_service
        recognition_service = get_recognition_service()
        recognition_service.stop_recognition(request.sid)
        emit('recognition_stopped', {'message': 'Recognition stopped'})
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error in stop_recognition: {e}")
        emit('error', {'message': 'Failed to stop recognition'})


@socketio.on('video_frame')
def handle_video_frame(data):
    """Handle video frame from client for recognition"""
    try:
        from flask_login import current_user
        from backend.services.face_recognition_service import get_recognition_service
        
        if not current_user.is_authenticated:
            return
        
        recognition_service = get_recognition_service()
        
        if not recognition_service.is_session_active(request.sid):
            return
        
        frame_data = data.get('frame')
        if not frame_data:
            return
        
        # Process frame (with proper error handling)
        result = recognition_service.process_frame(request.sid, frame_data)
        
        if result:
            # Emit recognition result
            emit('recognition_result', result)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.debug(f"Error in handle_video_frame: {e}")
        # Don't emit error to avoid spamming client
        pass

# Setup login manager user loader
@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    try:
        return User.query.get(int(user_id))
    except (ValueError, TypeError):
        return None
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error loading user {user_id}: {e}")
        return None


@app.route('/test')
def test():
    """Simple test route to verify server is working"""
    return "<h1>Server is working!</h1><p>If you see this, the server is responding.</p><a href='/'>Go to home</a>"

@app.route('/')
def index():
    """Root route - redirect based on user role"""
    from flask_login import current_user
    
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('driver.dashboard'))
    return redirect(url_for('auth.login'))


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    try:
        return render_template('errors/404.html'), 404
    except:
        return "<h1>404 - Page Not Found</h1><p>The page you're looking for doesn't exist.</p><p><a href='/'>Go Home</a></p>", 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    try:
        db.session.rollback()
    except:
        pass
    try:
        return render_template('errors/500.html'), 500
    except:
        return "<h1>500 Internal Server Error</h1><p>An error occurred. Please try again.</p><p><a href='/'>Go Home</a></p>", 500


def create_tables():
    """Create database tables"""
    with app.app_context():
        db.create_all()
        
        # Create default admin user if none exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            from werkzeug.security import generate_password_hash
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),  # Change in production!
                role='admin'
            )
            db.session.add(admin)
            
            # Create a sample driver
            driver = User(
                username='driver1',
                password_hash=generate_password_hash('driver123'),  # Change in production!
                role='driver'
            )
            db.session.add(driver)
            db.session.commit()
            print("✅ Default admin user created: username='admin', password='admin123'")
            print("✅ Default driver user created: username='driver1', password='driver123'")


if __name__ == '__main__':
    # Create tables on first run
    create_tables()
    
    # Run application
    print("\n" + "="*60)
    print("🚌 Bus Management System Starting...")
    print("="*60)
    print(f"📁 Database: {config.SQLALCHEMY_DATABASE_URI}")
    print(f"🌐 Running on: http://localhost:5000")
    print("="*60 + "\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=config.DEBUG)

