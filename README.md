# 🚌 Bus Management System with Face Recognition

A complete web-based bus management system with AI-powered face recognition for student authentication.

## 📋 Features

- **Admin Portal**: Manage students, buses, assignments, and view logs
- **Driver Portal**: Real-time face recognition for bus entry authentication
- **Face Recognition**: Integration with advanced face recognition system
- **Authentication Logs**: Track all entry attempts and access decisions
- **Student Management**: Upload photos, assign to buses, manage information
- **Bus Management**: Create buses, assign drivers, manage routes

## 🏗️ Architecture

- **Backend**: Flask (Python) with SQLAlchemy ORM
- **Frontend**: HTML/CSS/JavaScript with SocketIO for real-time updates
- **Database**: SQLite (development) - easily upgradeable to PostgreSQL
- **Face Recognition**: DeepFace-based recognition system

## 📁 Project Structure

```
bus_management_system/
├── backend/                    # Flask backend application
│   ├── app.py                  # Main Flask app
│   ├── models.py               # Database models
│   ├── routes/                 # API routes
│   │   ├── auth_routes.py     # Authentication
│   │   ├── admin_routes.py    # Admin features
│   │   └── driver_routes.py   # Driver features
│   └── services/              # Business logic
│       ├── student_service.py
│       ├── bus_service.py
│       └── face_recognition_service.py
│
├── frontend/                    # Web interface
│   ├── templates/             # HTML templates
│   │   ├── admin/            # Admin pages
│   │   ├── driver/           # Driver pages
│   │   └── auth/             # Login/Register
│   └── static/               # CSS, JS, images
│
├── face_recognition_package/    # Face recognition engine
│   ├── advanced_realtime_recognition.py
│   └── database/              # Face images database
│
├── utils/                      # Utility modules
│   ├── file_handler.py        # Image handling
│   └── face_recognition_service.py
│
├── uploads/students/           # Student photos (primary storage)
├── database/                   # SQLite database
├── config.py                   # Configuration
├── requirements.txt            # Python dependencies
├── run.py                      # Run script
└── verify_setup.py             # Verification script
```

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Installation

1. **Clone or navigate to the project directory**

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install face recognition dependencies:**
   ```bash
   cd face_recognition_package
   pip install -r requirements.txt
   cd ..
   ```

4. **Verify setup:**
   ```bash
   python verify_setup.py
   ```
   This will check all connections and file structure.

### Running the Application

**Option 1: Using run script (recommended)**
```bash
python run.py
```

**Option 2: Direct Flask app**
```bash
python backend/app.py
```

The application will start on `http://localhost:5000`

### Default Login Credentials

**Admin:**
- Username: `admin`
- Password: `admin123`

**Driver:**
- Username: `driver1`
- Password: `driver123`

⚠️ **Important**: Change these passwords in production!

## 📝 Usage Guide

### Admin Features

1. **Login** as admin
2. **Dashboard**: View statistics and recent logs
3. **Student Management**: 
   - Add students with photos (2-3 recommended)
   - Edit student information
   - Delete students
4. **Bus Management**:
   - Create buses with routes
   - Assign drivers
   - Assign students to buses
5. **User Management**: Register new drivers/admins
6. **Authentication Logs**: View all recognition events

### Driver Features

1. **Login** as driver
2. **Dashboard**: View your bus and today's statistics
3. **Face Scanning**:
   - Click "Start Face Scanning"
   - Allow camera access
   - System recognizes students in real-time
   - Approve or deny access based on bus assignment

## 🔧 Configuration

Edit `config.py` to customize:

- Database path
- Upload folder location
- Session settings
- Secret key (change in production!)

## 🧪 Testing

Run the verification script to check everything:
```bash
python verify_setup.py
```

## 📊 Database Schema

- **users**: Admin and driver accounts
- **students**: Student information and photos
- **buses**: Bus details and routes
- **student_bus_assignments**: Many-to-many relationship
- **authentication_logs**: All recognition events

## 🔐 Security Notes

- Passwords are hashed using Werkzeug
- Session-based authentication
- Admin-only routes protected
- File upload validation
- SQL injection protection (ORM)

## 🐛 Troubleshooting

### "Module not found" errors
- Install dependencies: `pip install -r requirements.txt`
- Install face recognition dependencies: `cd face_recognition_package && pip install -r requirements.txt`

### Camera not working
- Ensure browser has camera permissions
- Check camera is not used by another application
- Try different browser (Chrome recommended)

### Face recognition not working
- Ensure DeepFace and dependencies are installed
- Check `face_recognition_package/database/` has student photos
- Photos should be organized by student name folders

### Database errors
- Delete `database/bus_management.db` and restart
- Check database permissions

## 📚 Documentation

- `BUS_MANAGEMENT_INTEGRATION_PLAN.md` - Complete integration documentation
- `INTEGRATION_SETUP.md` - Setup and utilities guide

## 🛠️ Development

### Adding new features

1. Models: Add to `backend/models.py`
2. Routes: Add to appropriate file in `backend/routes/`
3. Services: Add business logic to `backend/services/`
4. Templates: Add HTML to `frontend/templates/`

### Database migrations

Currently using SQLAlchemy auto-create. For production, consider:
- Flask-Migrate for versioned migrations
- PostgreSQL instead of SQLite

## 📄 License

This project is provided as-is for educational and development purposes.

## 🤝 Support

For issues or questions:
1. Check `BUS_MANAGEMENT_INTEGRATION_PLAN.md` for detailed documentation
2. Run `python verify_setup.py` to diagnose issues
3. Check logs in the console output

---

**Status**: ✅ All core features implemented and tested
**Version**: 1.0.0
**Last Updated**: 2025

