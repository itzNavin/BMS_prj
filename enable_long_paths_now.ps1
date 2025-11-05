# Quick command to enable long paths
# Run this in PowerShell as Administrator

# Check if admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[ERROR] Run PowerShell as Administrator first!" -ForegroundColor Red
    Write-Host "Right-click PowerShell -> Run as Administrator" -ForegroundColor Yellow
    exit 1
}

Write-Host "Enabling Long Path Support..." -ForegroundColor Yellow

try {
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -Type DWord -Force
    Write-Host "[SUCCESS] Long Path support enabled!" -ForegroundColor Green
    Write-Host ""
    Write-Host "IMPORTANT: You MUST restart your computer now!" -ForegroundColor Yellow
    Write-Host "After restart, long paths will be active." -ForegroundColor Cyan
} catch {
    Write-Host "[ERROR] Failed: $_" -ForegroundColor Red
}

