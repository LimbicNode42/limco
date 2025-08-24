#!/usr/bin/env python3
"""
Quick test to check if the repaired clone can be mounted
"""
import os
import subprocess

def test_clone_mount(clone_path):
    """Test if clone can be mounted by Windows."""
    print(f"[TEST] Testing mount capability: {os.path.basename(clone_path)}")
    
    if not os.path.exists(clone_path):
        print(f"[ERROR] Clone file not found: {clone_path}")
        return False
    
    file_size_gb = os.path.getsize(clone_path) / (1024**3)
    print(f"[INFO] Clone size: {file_size_gb:.2f} GB")
    
    # Test PowerShell mount
    abs_path = os.path.abspath(clone_path)
    ps_script = f'''
    try {{
        Write-Output "Testing mount for: {abs_path}"
        $mountResult = Mount-DiskImage -ImagePath "{abs_path}" -PassThru -ErrorAction Stop
        Write-Output "SUCCESS: Mount successful"
        
        # Try to get volume info
        Start-Sleep -Seconds 2
        $volumes = Get-Volume -DiskImage $mountResult -ErrorAction SilentlyContinue
        foreach ($vol in $volumes) {{
            Write-Output "VOLUME: $($vol.DriveLetter) - $($vol.FileSystemType) - $($vol.Size/1GB) GB"
        }}
        
        # Unmount
        Dismount-DiskImage -ImagePath "{abs_path}" -ErrorAction SilentlyContinue
        Write-Output "DISMOUNT: Complete"
        
    }} catch {{
        Write-Output "ERROR: $($_.Exception.Message)"
        Write-Output "TYPE: $($_.Exception.GetType().Name)"
    }}
    '''
    
    try:
        result = subprocess.run(['powershell', '-Command', ps_script], 
                               capture_output=True, text=True, timeout=60)
        
        print(f"[RESULT] PowerShell return code: {result.returncode}")
        print(f"[OUTPUT]")
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                print(f"   {line.strip()}")
        
        if result.stderr:
            print(f"[STDERR] {result.stderr}")
        
        # Check if mount was successful
        if "SUCCESS: Mount successful" in result.stdout:
            print(f"\n[VERDICT] ✅ CLONE IS MOUNTABLE - Ready for SD card!")
            return True
        else:
            print(f"\n[VERDICT] ❌ CLONE STILL HAS MOUNTING ISSUES")
            return False
            
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python test_mount.py <clone_path>")
        sys.exit(1)
    
    clone_path = sys.argv[1]
    success = test_clone_mount(clone_path)
    sys.exit(0 if success else 1)
