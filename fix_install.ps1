# Quick Fix Script for TensorFlow Installation
# Run this as Administrator

Write-Host "="*60
Write-Host "TensorFlow Installation Fix"
Write-Host "="*60
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[ERROR] Please run PowerShell as Administrator!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Right-click PowerShell -> Run as Administrator" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "[1/2] Enabling Windows Long Path Support..." -ForegroundColor Yellow

# Enable Long Path support
try {
    $longPath = Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -ErrorAction SilentlyContinue
    
    if ($longPath -and $longPath.LongPathsEnabled -eq 1) {
        Write-Host "[OK] Long Path support already enabled!" -ForegroundColor Green
    } else {
        Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -Type DWord
        Write-Host "[OK] Long Path support enabled!" -ForegroundColor Green
        Write-Host ""
        Write-Host "[!] IMPORTANT: You MUST restart your computer for this to work!" -ForegroundColor Yellow
        Write-Host ""
    }
} catch {
    Write-Host "[ERROR] Failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[2/2] Installing TensorFlow (CPU version for Python 3.13 compatibility)..." -ForegroundColor Yellow
Write-Host ""

# Install TensorFlow CPU version (better compatibility with Python 3.13)
pip install tensorflow-cpu

Write-Host ""
Write-Host "="*60
Write-Host "[SUCCESS] Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. If you enabled long paths, RESTART your computer" -ForegroundColor Yellow
Write-Host "2. After restart, install remaining dependencies:" -ForegroundColor Yellow
Write-Host "   pip install -r face_recognition_package/requirements.txt" -ForegroundColor White
Write-Host "="*60

