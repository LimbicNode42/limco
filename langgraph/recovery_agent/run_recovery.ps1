# PowerShell script to run CLI recovery tool as Administrator
# Right-click this file and select "Run with PowerShell" (will prompt for admin)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "CLI Drive Recovery Tool (PowerShell)" -ForegroundColor Cyan  
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "This script requires Administrator privileges." -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator or right-click this file and 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host "✅ Running with Administrator privileges" -ForegroundColor Green
Write-Host ""

# Change to script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "📁 Current directory: $ScriptDir" -ForegroundColor Yellow
Write-Host ""

# Show available commands
Write-Host "Available commands:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Scan drives:"
Write-Host "   python cli_recovery.py --scan-drives" -ForegroundColor White
Write-Host ""
Write-Host "2. Analyze specific drive:"
Write-Host "   python cli_recovery.py --analyze-only --source \\.\PhysicalDriveX" -ForegroundColor White
Write-Host ""  
Write-Host "3. Full recovery (analyze + clone):"
Write-Host "   python cli_recovery.py --recover --source \\.\PhysicalDriveX --output ./recovery" -ForegroundColor White
Write-Host ""
Write-Host "Replace X with your drive number (e.g., PhysicalDrive7)" -ForegroundColor Yellow
Write-Host ""

# Quick scan option
Write-Host "Quick start - scan drives now? (y/n): " -NoNewline -ForegroundColor Green
$response = Read-Host

if ($response -eq "y" -or $response -eq "Y") {
    Write-Host ""
    Write-Host "🔍 Scanning drives..." -ForegroundColor Cyan
    python cli_recovery.py --scan-drives
    Write-Host ""
}

Write-Host "Keep this window open to run more commands..." -ForegroundColor Green
Write-Host "Type 'exit' to close" -ForegroundColor Yellow

# Keep window open for more commands
while ($true) {
    $command = Read-Host "PS Recovery"
    
    if ($command -eq "exit") {
        break
    } elseif ($command.Trim() -eq "") {
        continue
    } elseif ($command.StartsWith("python cli_recovery.py")) {
        Invoke-Expression $command
    } else {
        Write-Host "Invalid command. Use: python cli_recovery.py [options]" -ForegroundColor Red
        Write-Host "Or type 'exit' to quit" -ForegroundColor Yellow
    }
    Write-Host ""
}
