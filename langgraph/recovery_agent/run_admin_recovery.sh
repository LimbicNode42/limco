#!/bin/bash
# Bash script to run CLI recovery tool with administrator privileges
# Usage: ./run_admin_recovery.sh [options]

echo "========================================="
echo "CLI Recovery Tool - Admin Launcher"
echo "========================================="
echo ""

# Check if we're on Windows
if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "cygwin" ]]; then
    echo "[ERROR] This script is designed for Windows bash terminals (Git Bash, MSYS2, etc.)"
    exit 1
fi

# Get the current directory in Windows format
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -W 2>/dev/null || pwd)"

echo "[DIR] Script directory: $SCRIPT_DIR"
echo "[INFO] Preparing to run with administrator privileges..."
echo ""

# Function to run a command as admin
run_as_admin() {
    local cmd="$1"
    echo "[EXEC] Executing as Administrator: $cmd"
    echo ""
    
    # Use PowerShell to elevate and run the command - keep window open on both success and error
    powershell.exe -Command "Start-Process cmd -ArgumentList '/k cd /d \"$SCRIPT_DIR\" && echo [ADMIN] Running: $cmd && $cmd && echo. && echo [COMPLETE] Command finished. Press any key to close... && pause >nul || (echo. && echo [ERROR] Command failed! && echo Press any key to close... && pause >nul)' -Verb RunAs"
}

# Function to show menu
show_menu() {
    echo "Choose an option:"
    echo "1. Scan drives"
    echo "2. Analyze SD card (PhysicalDrive7) only"
    echo "3. Full recovery of SD card (analyze + clone)"
    echo "4. Custom command"
    echo "5. Exit"
    echo ""
    echo -n "Enter your choice (1-5): "
}

# Main menu loop
while true; do
    show_menu
    read -r choice
    
    case $choice in
        1)
            echo ""
            run_as_admin "python cli_recovery.py --scan-drives"
            ;;
        2)
            echo ""
            run_as_admin "python cli_recovery.py --analyze-only --source \\\\.\\PhysicalDrive7"
            ;;
        3)
            echo ""
            echo "[WARN] This will create a full clone of your SD card!"
            echo -n "Are you sure you want to proceed? (y/N): "
            read -r confirm
            if [[ $confirm =~ ^[Yy]$ ]]; then
                run_as_admin "python cli_recovery.py --recover --source \\\\.\\PhysicalDrive7 --output ./sd_recovery"
            else
                echo "Cancelled."
            fi
            ;;
        4)
            echo ""
            echo "Enter custom cli_recovery.py command (without 'python cli_recovery.py'):"
            echo "Example: --analyze-only --source \\\\.\\PhysicalDrive5"
            echo -n "> "
            read -r custom_args
            if [[ -n "$custom_args" ]]; then
                run_as_admin "python cli_recovery.py $custom_args"
            fi
            ;;
        5)
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo "[ERROR] Invalid choice. Please try again."
            echo ""
            ;;
    esac
    
    echo ""
    echo "Press Enter to continue..."
    read -r
    echo ""
done
