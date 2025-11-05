# Advanced Real-Time Face Recognition System

A production-ready, real-time face recognition system with automatic database refresh and optimized performance.

## 📋 Features

- ✅ Real-time face detection and recognition
- ✅ Multi-threaded processing for optimal performance
- ✅ Automatic database refresh when new faces are added
- ✅ Configurable recognition models and thresholds
- ✅ Clean, minimal display (bounding box, name, recognition rate)
- ✅ Comprehensive error handling and logging

## 🚀 Quick Start

### Step 1: Install Python Dependencies

Make sure you have Python 3.7 or higher installed, then run:

```bash
pip install -r requirements.txt
```

This will install all required packages including:
- DeepFace (face recognition library)
- OpenCV (computer vision)
- TensorFlow (deep learning framework)
- Other dependencies

**Note:** First-time installation may take a few minutes as it downloads AI models.

### Step 2: Setup Your Face Database

1. Add face images to the `database/` folder
2. Supported formats: `.jpg`, `.jpeg`, `.png`, `.bmp`
3. **Best practices:**
   - Use clear, front-facing photos
   - Good lighting, neutral expression
   - Minimum resolution: 200x200 pixels
   - 2-3 images per person for better accuracy

**Database structure examples:**

```
database/
├── person1.jpg
├── person2.jpg
├── person3.jpg
└── naveen.jpg
```

Or organized by person:

```
database/
├── alice/
│   ├── photo1.jpg
│   └── photo2.jpg
└── bob/
    ├── photo1.jpg
    └── photo2.jpg
```

### Step 3: Configure Settings (Optional)

Edit `recognition_config.json` to customize:

- **Camera source**: Change `camera_source` (0 = default camera, 1 = second camera)
- **Recognition model**: `VGG-Face` (default), `Facenet512`, `ArcFace`, etc.
- **Confidence threshold**: Minimum confidence to accept match (default: 60.0)
- **Performance**: Adjust `frame_skip` (higher = faster but less responsive)

See `recognition_config.json` for all available options.

### Step 4: Run the System

```bash
python advanced_realtime_recognition.py
```

**That's it!** The system will:
- Load face recognition models
- Open your camera
- Detect and recognize faces in real-time
- Display names and recognition rate

**Controls:**
- Press **'q'** to quit
- Press **'r'** to reset statistics
- Press **'f'** to manually refresh database (after adding new faces)

## 📊 What's Displayed

- **Bounding Box**: Green rectangle around recognized faces
- **Name Label**: Person's name with confidence percentage (e.g., "naveen: 62.8%")
- **Recognition Rate**: Success percentage (top-left corner)

## 🔧 Adding New Faces

### Method 1: Automatic Refresh (Recommended)
1. The system automatically detects when new images are added
2. Database refreshes automatically (checks every 5 seconds)
3. New faces are recognized immediately

### Method 2: Manual Refresh
1. Add new face images to `database/` folder
2. Press **'f'** during runtime to refresh database
3. Wait for processing to complete (~10-30 seconds depending on number of images)

## ⚙️ Configuration Options

Edit `recognition_config.json` to customize:

### Performance Settings
```json
{
  "frame_skip": 5,              // Process every Nth frame (higher = faster)
  "confidence_threshold": 60.0,  // Minimum confidence (0-100)
  "max_recognition_threads": 2   // Number of processing threads
}
```

### Recognition Models
- **VGG-Face**: Fast, good accuracy (default, recommended)
- **Facenet512**: High accuracy, slower
- **ArcFace**: Very high accuracy, slower

### Detector Backends
- **opencv**: Fastest (default)
- **retinaface**: Most accurate, slower

## 🐛 Troubleshooting

### Camera Not Opening
- Check if camera is not in use by another application
- Try different camera index: change `camera_source` to 1, 2, etc.
- On Linux, you may need camera permissions

### Slow Performance
- Increase `frame_skip` in config (e.g., 5 → 10)
- Use `opencv` detector instead of `retinaface`
- Reduce camera resolution

### Poor Recognition Accuracy
- Improve database image quality (better lighting, front-facing)
- Use more images per person (2-3 recommended)
- Lower `confidence_threshold` (but may have false positives)
- Try better model: `Facenet512` or `ArcFace`

### Database Refresh Not Working
- Press **'f'** to manually refresh
- Check that `auto_refresh_database` is `true` in config
- Wait a few seconds after adding images

## 📁 Project Structure

```
face_recognition_package/
├── advanced_realtime_recognition.py  # Main system
├── recognition_config.json           # Configuration file
├── requirements.txt                  # Python dependencies
├── README.md                         # This file
└── database/                         # Face images folder
    ├── person1.jpg
    ├── person2.jpg
    └── ...
```

## 📝 Output Files

- **face_recognition.log**: System logs and events
- **recognition_log_YYYYMMDD_HHMMSS.json**: Recognition history (if enabled)

## 🔒 Privacy & Security

- All processing is done locally on your machine
- No data is sent to external servers
- Face images are stored locally in `database/` folder
- Recognition logs are optional and stored locally

## 📚 System Requirements

- **Python**: 3.7 or higher
- **Operating System**: Windows, Linux, or macOS
- **RAM**: 4GB minimum (8GB recommended)
- **Camera**: USB webcam or built-in camera
- **Disk Space**: ~2GB for models (first-time download)

## 🆘 Need Help?

1. Check the troubleshooting section above
2. Review `recognition_config.json` settings
3. Check `face_recognition.log` for error messages
4. Ensure all dependencies are installed: `pip install -r requirements.txt`

## 📄 License

This implementation uses DeepFace library. Please refer to DeepFace license for details.

---

**Ready to use!** Just run `python advanced_realtime_recognition.py` and start recognizing faces! 🚀

