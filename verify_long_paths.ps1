# Verify Long Path Support is Enabled
# Run this after restarting your computer

Write-Host "Checking Long Path Support Status..." -ForegroundColor Cyan
Write-Host ""

$longPath = Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -ErrorAction SilentlyContinue

if ($longPath -and $longPath.LongPathsEnabled -eq 1) {
    Write-Host "[SUCCESS] Long Path Support is ENABLED!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Status: Enabled (1)" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now install packages with long paths:" -ForegroundColor Cyan
    Write-Host "  pip install -r requirements.txt" -ForegroundColor White
    Write-Host "  cd face_recognition_package" -ForegroundColor White
    Write-Host "  pip install -r requirements.txt" -ForegroundColor White
} else {
    Write-Host "[WARNING] Long Path Support is NOT enabled" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Status: Disabled (0 or not found)" -ForegroundColor Red
    Write-Host ""
    Write-Host "If you just enabled it, make sure you restarted your computer." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" * 60

