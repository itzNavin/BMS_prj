# PowerShell script to enable Windows Long Path support
# Run this as Administrator

Write-Host "="*60
Write-Host "Windows Long Path Support Fix"
Write-Host "="*60
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[ERROR] This script must be run as Administrator!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Right-click PowerShell and select 'Run as Administrator', then run this script again."
    Write-Host ""
    pause
    exit 1
}

Write-Host "[INFO] Checking current Long Path setting..." -ForegroundColor Yellow

# Check current setting
$current = (Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -ErrorAction SilentlyContinue)

if ($current -and $current.LongPathsEnabled -eq 1) {
    Write-Host "[OK] Long Path support is already enabled!" -ForegroundColor Green
    Write-Host ""
    Write-Host "You may need to restart your computer for changes to take effect."
} else {
    Write-Host "[INFO] Enabling Long Path support..." -ForegroundColor Yellow
    
    try {
        # Enable Long Path support
        Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -Type DWord
        
        Write-Host "[SUCCESS] Long Path support enabled!" -ForegroundColor Green
        Write-Host ""
        Write-Host "IMPORTANT: You MUST restart your computer for this to take effect." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "After restarting, try installing the packages again:"
        Write-Host "  pip install -r face_recognition_package/requirements.txt"
        Write-Host ""
        
        $restart = Read-Host "Would you like to restart now? (Y/N)"
        if ($restart -eq 'Y' -or $restart -eq 'y') {
            Restart-Computer
        }
    } catch {
        Write-Host "[ERROR] Failed to enable Long Path support: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "You can manually enable it by:"
        Write-Host "1. Open Registry Editor (regedit)"
        Write-Host "2. Navigate to: HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem"
        Write-Host "3. Create or set DWORD: LongPathsEnabled = 1"
        Write-Host "4. Restart computer"
    }
}

Write-Host ""
Write-Host "="*60

