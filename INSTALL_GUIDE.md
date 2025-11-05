# Installation Guide - Windows Long Path Issue Fix

## Problem

You're encountering this error when installing TensorFlow:
```
ERROR: Could not install packages due to an OSError: [Errno 2] No such file or directory
HINT: This error might have occurred since this system does not have Windows Long Path support enabled.
```

This happens because:
1. Your project path is long: `C:\Users\91821\OneDrive\my_projects\face_recog_projects\Bus management system\`
2. TensorFlow has very long internal file paths
3. Windows default path limit is 260 characters

## Solutions

### Solution 1: Enable Windows Long Path Support (Recommended)

**Option A: Using PowerShell Script (Easiest)**

1. Right-click PowerShell and select **"Run as Administrator"**
2. Navigate to project directory:
   ```powershell
   cd "C:\Users\91821\OneDrive\my_projects\face_recog_projects\Bus management system"
   ```
3. Run the fix script:
   ```powershell
   .\fix_windows_long_paths.ps1
   ```
4. **Restart your computer** (required!)
5. After restart, try installing again:
   ```powershell
   pip install -r face_recognition_package/requirements.txt
   ```

**Option B: Manual Registry Edit**

1. Press `Win + R`, type `regedit`, press Enter
2. Navigate to: `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem`
3. Look for `LongPathsEnabled` (or create it as DWORD if it doesn't exist)
4. Set value to `1`
5. **Restart your computer**
6. Try installing again

**Option C: Using Group Policy (Windows 10 Pro/Enterprise)**

1. Press `Win + R`, type `gpedit.msc`, press Enter
2. Navigate to: `Computer Configuration → Administrative Templates → System → Filesystem`
3. Enable "Enable Win32 long paths"
4. **Restart your computer**

### Solution 2: Move Project to Shorter Path (Quick Fix)

If you can't enable long paths, move the project to a shorter path:

```powershell
# Create shorter path
New-Item -ItemType Directory -Path "C:\Projects\BusSystem" -Force

# Move project (or copy if you prefer)
Move-Item -Path "C:\Users\91821\OneDrive\my_projects\face_recog_projects\Bus management system" -Destination "C:\Projects\BusSystem\" -Force

# Navigate to new location
cd C:\Projects\BusSystem
```

Then install from the new location.

### Solution 3: Install TensorFlow Separately (Alternative)

If you continue having issues, try installing TensorFlow separately:

```powershell
# Install TensorFlow first (may have different path handling)
pip install tensorflow

# Then install other dependencies
pip install -r face_recognition_package/requirements.txt
```

Or use a lighter TensorFlow version:

```powershell
# Install TensorFlow Lite or CPU-only version
pip install tensorflow-cpu
```

## Verification

After enabling long paths and restarting, verify it worked:

```powershell
# Check registry setting
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled"
```

Should show `LongPathsEnabled : 1`

## Installation Steps (After Fix)

Once long paths are enabled:

1. **Install main dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Install face recognition dependencies:**
   ```powershell
   cd face_recognition_package
   pip install -r requirements.txt
   cd ..
   ```

3. **Verify installation:**
   ```powershell
   python verify_setup.py
   ```

## Troubleshooting

### Still Getting Errors After Enabling Long Paths?

1. **Make sure you restarted** - Long paths only work after restart
2. **Check Python version** - TensorFlow requires Python 3.8-3.11 (you have 3.13)
3. **Try TensorFlow 2.15 or earlier** for Python 3.13 compatibility

```powershell
# Install specific TensorFlow version
pip install tensorflow==2.15.0
```

### Alternative: Use Virtual Environment in Shorter Path

```powershell
# Create venv in shorter path
cd C:\
python -m venv bus_venv
.\bus_venv\Scripts\Activate.ps1

# Install packages
cd "C:\Projects\BusSystem"  # or your project path
pip install -r requirements.txt
```

## Notes

- **OneDrive paths are often long** - Consider moving project outside OneDrive
- **Long path support requires Windows 10 version 1607 or later**
- **Some older tools may still have issues** even with long paths enabled

## Need Help?

If issues persist:
1. Check Windows version: `winver` (must be 1607+)
2. Try installing in a shorter path
3. Use TensorFlow CPU-only version if GPU isn't needed
4. Consider using a virtual environment in a shorter location

---

**Recommended**: Enable long paths (Solution 1) + Restart, then install from project directory.

