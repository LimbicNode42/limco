#!/bin/bash
# Simple script to launch an admin bash terminal for recovery operations
# This will open a new elevated bash window

echo "🚀 Launching Administrator Bash Terminal..."
echo ""

# Get current directory
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -W 2>/dev/null || pwd)"

# Launch elevated bash terminal
powershell.exe -Command "Start-Process 'C:\\Program Files\\Git\\bin\\bash.exe' -ArgumentList '--login -i -c \"cd \\\"$CURRENT_DIR\\\" && echo \\\"✅ Administrator Bash Terminal\\\" && echo \\\"📁 Current directory: \$(pwd)\\\" && echo \\\"🛠️  You can now run:\\\" && echo \\\"   python cli_recovery.py --scan-drives\\\" && echo \\\"   python cli_recovery.py --recover --source \\\\\\\\.\\\\PhysicalDrive7 --output ./sd_recovery\\\" && echo \\\"\\\" && exec bash\"' -Verb RunAs"

echo "✅ Admin terminal should open in a new window"
echo "   If it doesn't appear, check your taskbar"
