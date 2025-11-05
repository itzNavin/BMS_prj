# 🚨 What's Wrong & How to Fix It

## The Problem

You're getting this error:
```
ERROR: Could not install packages due to an OSError: [Errno 2] No such file or directory
HINT: This error might have occurred since this system does not have Windows Long Path support enabled.
```

## Why This Happened

1. **Windows Path Limit**: Windows has a 260-character limit for file paths by default
2. **Long Project Path**: Your project is in a deep folder structure
3. **TensorFlow Long Paths**: TensorFlow creates files with very long internal paths
4. **Python 3.13**: Very new version - TensorFlow compatibility may be limited

## ✅ EASIEST FIX (3 Steps)

### Step 1: Enable Long Path Support (Run as Administrator)

**Right-click PowerShell → "Run as Administrator"**, then run:

```powershell
cd "C:\Users\91821\OneDrive\my_projects\face_recog_projects\Bus management system"
.\fix_install.ps1
```

**OR manually:**
```powershell
# Run as Administrator
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

### Step 2: Restart Your Computer
⚠️ **This is required!** Long paths only work after restart.

### Step 3: Install Dependencies

After restart, run:
```powershell
cd "C:\Users\91821\OneDrive\my_projects\face_recog_projects\Bus management system"

# Install main dependencies
pip install -r requirements.txt

# Install face recognition dependencies (will work now)
cd face_recognition_package
pip install -r requirements.txt
cd ..
```

## 🎯 Alternative: Use TensorFlow CPU Version

If you want to avoid long paths, use TensorFlow CPU version (lighter, better Python 3.13 support):

```powershell
# Install TensorFlow CPU version first
pip install tensorflow-cpu

# Then install other dependencies
pip install -r face_recognition_package/requirements.txt
```

## 📋 Summary

**What to do RIGHT NOW:**

1. ✅ **Enable long paths** (run as Administrator)
2. ✅ **Restart computer**
3. ✅ **Install dependencies** (after restart)

**OR:**

1. ✅ **Install TensorFlow CPU** first: `pip install tensorflow-cpu`
2. ✅ **Then install other packages**

---

**The fix script (`fix_install.ps1`) will do steps 1 for you automatically!**

