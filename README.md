# 🚌 Bus Management System with Face Recognition

A complete web-based bus management system with AI-powered face recognition for student authentication and access control.

## 📋 Table of Contents

- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Default Credentials](#default-credentials)
- [Usage Guide](#usage-guide)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Technical Details](#technical-details)

## ✨ Features

### Admin Portal
- **Student Management**: Add, edit, and delete students with photo uploads
- **Bus Management**: Create buses, assign routes, and manage capacity
- **Driver Management**: Create and manage driver accounts
- **Student-Bus Assignment**: Assign students to specific buses
- **Authentication Logs**: View all face recognition events with filtering
- **Clear Logs**: Remove all authentication logs when needed
- **Dashboard**: View statistics and recent activity

### Driver Portal
- **Real-time Face Recognition**: Live camera feed with instant student recognition
- **Access Control**: Automatically grant/deny access based on bus assignments
- **Today's Statistics**: View granted/denied entries for the day
- **Clear Today's Entries**: Remove all today's logs for the driver
- **Bus Information**: View assigned bus details and student count

### Face Recognition System
- **AI-Powered Recognition**: DeepFace-based face recognition engine
- **Real-time Processing**: Live video stream analysis
- **High Accuracy**: Configurable confidence thresholds
- **Automatic Database Sync**: Updates when new students are added

## 💻 System Requirements

- **Python**: 3.7 or higher (3.8+ recommended)
- **Operating System**: Windows, Linux, or macOS
- **RAM**: Minimum 4GB (8GB recommended for face recognition)
- **Storage**: At least 2GB free space
- **Web Browser**: Chrome, Firefox, or Edge (latest versions)
- **Camera**: For driver face scanning feature

## 🚀 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/itzNavin/BMS_prj.git
cd BMS_prj
```

### Step 2: Create Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Main Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install Face Recognition Dependencies

```bash
cd face_recognition_package
pip install -r requirements.txt
cd ..
```

**Note**: Face recognition dependencies may take 10-15 minutes to install. This includes TensorFlow, OpenCV, and DeepFace libraries.

### Step 5: Verify Installation

```bash
python verify_setup.py
```

This will check:
- All required directories exist
- Configuration is valid
- Database models are correct
- Routes and services are properly set up
- Templates and static files are present

## ⚙️ Configuration

The application uses `config.py` for configuration. Default settings should work for most installations.

### Important Settings

**Database Path:**
```python
SQLALCHEMY_DATABASE_URI = 'sqlite:///database/bus_management.db'
```

**Upload Folder:**
```python
UPLOAD_FOLDER = 'uploads/students'
```

**Face Recognition Database:**
```python
FACE_RECOGNITION_DB = 'face_recognition_package/database'
```

**Secret Key (Change in Production!):**
```python
SECRET_KEY = 'your-secret-key-here'  # Change this!
```

### Database Connection Pooling

For better performance with face recognition, the system uses:
- Pool size: 20 connections
- Max overflow: 40 connections
- Connection recycling: Every hour

## 🏃 Running the Application

### Option 1: Using Run Script (Recommended)

```bash
python run.py
```

### Option 2: Direct Flask Application

```bash
python backend/app.py
```

The application will start on: **http://localhost:5000**

### Stopping the Application

Press **Ctrl+C** in the terminal. The application will gracefully shut down all active sessions.

## 🔑 Default Credentials

**⚠️ IMPORTANT: Change these passwords in production!**

### Admin Account
- **Username**: `admin`
- **Password**: `admin123`

### Driver Account
- **Username**: `driver1`
- **Password**: `driver123`

## 📖 Usage Guide

### For Administrators

1. **Login** as admin using the default credentials
2. **Add Students**:
   - Go to "Add Student" in Quick Actions
   - Enter student ID, name, class, and section
   - Upload 2-3 photos of the student (front-facing, clear face)
   - Click "Add Student"
3. **Create Buses**:
   - Click "Add Bus"
   - Enter bus number, route name, and capacity
   - Optionally assign a driver
4. **Assign Students to Buses**:
   - Go to "Manage Buses"
   - Click "Assign Students" on a bus
   - Select students and save
5. **Add Drivers**:
   - Click "Add Driver" in Quick Actions
   - Enter username and password
   - Driver can now log in
6. **View Logs**:
   - Click "View Logs" to see all authentication events
   - Use "Clear Logs" to remove all entries

### For Drivers

1. **Login** as driver
2. **View Dashboard**:
   - See your assigned bus information
   - Check today's statistics
3. **Start Face Scanning**:
   - Click "Start Face Scanning"
   - Allow camera access when prompted
   - Point camera at student's face
   - System automatically recognizes and checks bus assignment
   - Access is granted or denied automatically
4. **Clear Today's Entries**:
   - Click "Clear Today's Entries" to remove all logs for today

## 📁 Project Structure

```
bus_management_system/
├── backend/                      # Flask backend application
│   ├── app.py                   # Main Flask application
│   ├── models.py                # Database models (User, Student, Bus, etc.)
│   ├── routes/                  # API routes
│   │   ├── auth_routes.py      # Authentication routes
│   │   ├── admin_routes.py     # Admin features
│   │   └── driver_routes.py    # Driver features
│   └── services/               # Business logic layer
│       ├── student_service.py  # Student operations
│       ├── bus_service.py      # Bus operations
│       └── face_recognition_service.py  # Face recognition integration
│
├── frontend/                     # Web interface
│   ├── templates/              # HTML templates
│   │   ├── admin/             # Admin pages
│   │   ├── driver/            # Driver pages
│   │   ├── auth/              # Login/Register
│   │   └── base.html          # Base template
│   └── static/                # Static files
│       ├── css/style.css      # Styles
│       └── js/                # JavaScript
│           ├── main.js        # Main scripts
│           └── face_scanning.js  # Face scanning logic
│
├── face_recognition_package/     # Face recognition engine
│   ├── advanced_realtime_recognition.py  # Recognition system
│   ├── database/               # Face images database
│   │   └── [student_name]/    # Student folders with photos
│   ├── recognition_config.json  # Recognition settings
│   └── requirements.txt        # Face recognition dependencies
│
├── utils/                       # Utility modules
│   ├── file_handler.py         # File/image handling
│   └── face_recognition_service.py  # Face recognition wrapper
│
├── uploads/students/            # Student photo storage (primary)
├── database/                    # SQLite database
├── config.py                   # Configuration file
├── requirements.txt            # Main Python dependencies
├── run.py                      # Application entry point
├── verify_setup.py             # Setup verification script
└── README.md                   # This file
```

## 🔧 Troubleshooting

### "Module not found" Errors

**Solution:**
```bash
# Install main dependencies
pip install -r requirements.txt

# Install face recognition dependencies
cd face_recognition_package
pip install -r requirements.txt
cd ..
```

### Camera Not Working

**Symptoms**: Camera doesn't start or shows black screen

**Solutions:**
1. Check browser permissions (allow camera access)
2. Ensure camera is not used by another application
3. Try a different browser (Chrome recommended)
4. Check if camera drivers are installed

### Face Recognition Not Working

**Symptoms**: No recognition or "database empty" errors

**Solutions:**
1. Ensure students have photos uploaded (2-3 photos per student)
2. Check `face_recognition_package/database/` has student folders
3. Photos should be organized: `database/[student_name]/photo1.jpg`
4. Wait for database embeddings to generate (first time takes longer)
5. Check console for error messages

### Database Connection Errors

**Symptoms**: "QueuePool limit reached" or connection timeouts

**Solutions:**
1. Restart the application
2. Check if database file exists: `database/bus_management.db`
3. Delete database file and restart (will recreate automatically)
4. Check database permissions

### Slow Performance

**Solutions:**
1. Reduce camera resolution in browser settings
2. Close other applications using CPU/GPU
3. Ensure face recognition database is properly initialized
4. Check system resources (RAM, CPU)

### Installation Issues on Windows

If you encounter "path too long" errors during installation:

1. Enable Windows Long Path Support:
   - Open PowerShell as Administrator
   - Run: `New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force`
   - Restart computer

2. Or use a shorter project path

## 🔐 Security Notes

- **Passwords**: All passwords are hashed using Werkzeug's security functions
- **Sessions**: Session-based authentication with secure cookies
- **Access Control**: Admin routes protected with decorators
- **File Upload**: Validated file types and sizes
- **SQL Injection**: Protected by SQLAlchemy ORM
- **Secret Key**: Change `SECRET_KEY` in `config.py` for production

## 📊 Database Schema

### Tables

- **users**: Admin and driver accounts
- **students**: Student information (ID, name, class, section, photo path)
- **buses**: Bus details (number, route, driver, capacity)
- **student_bus_assignments**: Many-to-many relationship between students and buses
- **authentication_logs**: All face recognition events (timestamp, student, bus, driver, status)

## 🛠️ Technical Details

### Technology Stack

- **Backend**: Flask 3.0.0
- **Database**: SQLite (SQLAlchemy ORM)
- **Authentication**: Flask-Login
- **Real-time**: Flask-SocketIO (threading mode)
- **Face Recognition**: DeepFace with VGG-Face model
- **Image Processing**: OpenCV, TensorFlow

### Face Recognition Configuration

- **Model**: VGG-Face (default)
- **Detector**: OpenCV
- **Distance Metric**: Cosine
- **Confidence Threshold**: 60% (configurable)
- **Auto-refresh**: Enabled (updates when new students added)

### Performance

- **Connection Pool**: 20 base connections, 40 overflow
- **Session Cleanup**: Automatic after each request
- **Error Handling**: Graceful handling of OpenCV errors
- **Threading**: Multi-threaded face recognition processing

## 📚 Additional Documentation

- `BUS_MANAGEMENT_INTEGRATION_PLAN.md` - Detailed integration documentation
- `INTEGRATION_SETUP.md` - Setup and utilities guide

## 🤝 Support

If you encounter issues:

1. Run `python verify_setup.py` to diagnose problems
2. Check the console output for error messages
3. Review the troubleshooting section above
4. Ensure all dependencies are installed correctly

## 📄 License

This project is provided as-is for educational and development purposes.

## 🎯 Quick Checklist for New Installation

- [ ] Python 3.7+ installed
- [ ] Virtual environment created and activated
- [ ] Main dependencies installed (`requirements.txt`)
- [ ] Face recognition dependencies installed (`face_recognition_package/requirements.txt`)
- [ ] Setup verified (`python verify_setup.py`)
- [ ] Application runs (`python run.py`)
- [ ] Can access http://localhost:5000
- [ ] Can login with admin credentials
- [ ] Can add students with photos
- [ ] Camera works for face scanning

---

**Version**: 1.0.0  
**Last Updated**: November 2025  
**Status**: ✅ Production Ready
