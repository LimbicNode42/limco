@echo off
echo =====================================
echo CLI Drive Recovery Tool (Admin Mode)
echo =====================================
echo.
echo This tool requires Administrator privileges for drive access.
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Show available commands
echo Available commands:
echo.
echo 1. Scan drives:
echo    python cli_recovery.py --scan-drives
echo.
echo 2. Analyze drive only:
echo    python cli_recovery.py --analyze-only --source \\.\PhysicalDriveX
echo.
echo 3. Full recovery (analyze + clone):
echo    python cli_recovery.py --recover --source \\.\PhysicalDriveX --output ./recovery
echo.
echo Replace X with your drive number (e.g., PhysicalDrive7)
echo.

REM Keep window open
cmd /k
