# Setup and Installation Guide

This guide provides detailed setup instructions and troubleshooting tips.

## Quick Installation

```bash
# 1. Clone repository
git clone https://github.com/itzNavin/BMS_prj.git
cd BMS_prj

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt
cd face_recognition_package
pip install -r requirements.txt
cd ..

# 4. Verify setup
python verify_setup.py

# 5. Run application
python run.py
```

## Windows Long Path Issue

If you encounter "path too long" errors during installation:

### Enable Long Path Support (Recommended)

1. Open PowerShell as Administrator
2. Run:
   ```powershell
   New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
   ```
3. Restart your computer
4. Retry installation

### Alternative: Use Shorter Path

Move project to a shorter path like `C:\Projects\BusSystem`

## Directory Structure

The application uses two storage locations for student photos:

1. **`uploads/students/[student_id]/`** - Primary storage (by student ID)
2. **`face_recognition_package/database/[student_name]/`** - Face recognition database (by student name)

Both are automatically synchronized when students are added.

## Utilities

The `utils/` module provides helper functions:

- `save_student_photos()` - Save photos to uploads directory
- `copy_photos_to_face_db()` - Copy photos to face recognition database
- `BusFaceRecognitionService` - High-level face recognition service

## Verification

After installation, run:
```bash
python verify_setup.py
```

This checks:
- All directories exist
- Configuration is valid
- Database models are correct
- Routes and services are set up
- Templates and static files are present

## Troubleshooting

### Module Not Found Errors
- Ensure virtual environment is activated
- Install both requirements files (main + face_recognition_package)
- Check Python version (3.7+ required)

### Camera Not Working
- Allow camera permissions in browser
- Close other applications using camera
- Try Chrome browser (recommended)

### Face Recognition Not Working
- Ensure students have photos uploaded (2-3 per student)
- Check `face_recognition_package/database/` has student folders
- Wait for database embeddings to generate (first time takes longer)

For more details, see the main README.md file.

