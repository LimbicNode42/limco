# Quick test script to run recovery as admin
# Run this from an Administrator PowerShell/Command Prompt

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our CLI tool
from cli_recovery import CLIDriveRecovery

def test_admin_recovery():
    """Test the recovery tool with admin privileges."""
    print("[TEST] Testing CLI Recovery Tool with Admin Privileges")
    print("=" * 50)
    
    recovery = CLIDriveRecovery()
    
    # Check admin status
    if not recovery.system_info['is_admin']:
        print("[ERROR] Error: This test requires Administrator privileges")
        print("        Please run as Administrator and try again")
        return False
    
    print("[OK] Running with Administrator privileges")
    
    # Scan drives
    print("\n[SCAN] Scanning drives...")
    drives = recovery.scan_drives()
    recovery.display_drives(drives)
    
    # Find PhysicalDrive7 (your SD card)
    target_drive = None
    for drive in drives:
        if 'PhysicalDrive7' in drive['device']:
            target_drive = drive['device']
            break
    
    if not target_drive:
        print("[ERROR] Could not find PhysicalDrive7 (SD card)")
        return False
    
    print(f"\n[TARGET] Target drive found: {target_drive}")
    
    # Analyze the drive
    print(f"\n[ANALYZE] Analyzing {target_drive}...")
    analysis = recovery.analyze_drive(target_drive)
    recovery.display_analysis(analysis)
    
    # Ask user if they want to proceed with cloning
    print("\n" + "="*50)
    print("[CONFIRM] CLONING CONFIRMATION")
    print("="*50)
    print(f"Ready to create clone of: {target_drive}")
    print(f"Clone will be saved to: ./test_recovery/")
    print("\nThis will create a complete copy of your SD card.")
    print("The original drive will NOT be modified.")
    print("\nProceed with cloning? (y/N): ", end="")
    
    response = input().strip().lower()
    
    if response == 'y':
        print("\n[CLONE] Creating recovery clone...")
        clone_result = recovery.create_recovery_clone(
            target_drive, 
            "./test_recovery",
            "sd_card_clone.img"
        )
        recovery.display_clone_result(clone_result)
        
        if clone_result['success']:
            print("\n[SUCCESS] SUCCESS! Clone created successfully.")
            print("You can now work on the clone file safely.")
        else:
            print("\n[WARN] Clone creation had issues.")
            print("Check the AI suggestions above for next steps.")
    else:
        print("\n[STOP] Cloning cancelled by user.")
        print("Analysis complete. No changes made to your drive.")
    
    return True

if __name__ == "__main__":
    test_admin_recovery()
