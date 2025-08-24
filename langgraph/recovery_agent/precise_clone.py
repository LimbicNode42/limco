#!/usr/bin/env python3
"""
Precise Clone Tool - Clone only the actual drive size, not beyond
"""
import os
import subprocess
import struct
from typing import Optional

class PreciseCloner:
    def __init__(self):
        self.sector_size = 512
    
    def get_actual_drive_size(self, drive_path: str) -> Optional[int]:
        """Get the actual drive size using multiple methods."""
        print(f"[SIZE] Determining actual size of {drive_path}")
        
        # Method 1: Try PowerShell Get-Disk
        if 'PhysicalDrive' in drive_path:
            disk_num = drive_path.split('PhysicalDrive')[1]
            ps_script = f'''
try {{
    $disk = Get-Disk -Number {disk_num} -ErrorAction Stop
    Write-Host "SIZE:$($disk.Size)"
}} catch {{
    Write-Host "ERROR:$($_.Exception.Message)"
}}
'''
            try:
                result = subprocess.run(['powershell', '-Command', ps_script], 
                                       capture_output=True, text=True, timeout=30)
                
                for line in result.stdout.split('\n'):
                    if line.startswith('SIZE:'):
                        size = int(line.split(':')[1])
                        print(f"[SIZE] PowerShell reports: {size:,} bytes ({size / (1024**3):.2f} GB)")
                        return size
            except Exception as e:
                print(f"[SIZE] PowerShell method failed: {e}")
        
        # Method 2: Try WMI query
        if 'PhysicalDrive' in drive_path:
            disk_num = drive_path.split('PhysicalDrive')[1]
            ps_script = f'''
try {{
    $disk = Get-WmiObject -Class Win32_DiskDrive | Where-Object {{ $_.DeviceID -eq "\\\\.\\PHYSICALDRIVE{disk_num}" }}
    if ($disk) {{
        Write-Host "SIZE:$($disk.Size)"
    }} else {{
        Write-Host "ERROR:Disk not found"
    }}
}} catch {{
    Write-Host "ERROR:$($_.Exception.Message)"
}}
'''
            try:
                result = subprocess.run(['powershell', '-Command', ps_script], 
                                       capture_output=True, text=True, timeout=30)
                
                for line in result.stdout.split('\n'):
                    if line.startswith('SIZE:'):
                        size = int(line.split(':')[1])
                        print(f"[SIZE] WMI reports: {size:,} bytes ({size / (1024**3):.2f} GB)")
                        return size
            except Exception as e:
                print(f"[SIZE] WMI method failed: {e}")
        
        print(f"[SIZE] Could not determine actual drive size")
        return None
    
    def clone_precise_size(self, source_drive: str, output_path: str, max_size: int) -> bool:
        """Clone only up to the specified size."""
        print(f"[CLONE] Creating precise clone of {max_size:,} bytes ({max_size / (1024**3):.2f} GB)")
        
        # PowerShell script with size limit
        ps_script = f'''
try {{
    $sourcePath = "{source_drive}"
    $destPath = "{output_path}"
    $maxBytes = {max_size}
    
    Write-Host "[PS] Opening source: $sourcePath"
    $sourceStream = [System.IO.File]::OpenRead($sourcePath)
    
    Write-Host "[PS] Creating destination: $destPath"
    $destStream = [System.IO.File]::Create($destPath)
    
    Write-Host "[PS] Starting precise copy (limit: $maxBytes bytes)..."
    $buffer = New-Object byte[] 1048576  # 1MB buffer
    $totalBytes = 0
    
    while ($totalBytes -lt $maxBytes) {{
        $remainingBytes = $maxBytes - $totalBytes
        $bufferSize = [Math]::Min($buffer.Length, $remainingBytes)
        
        $bytesRead = $sourceStream.Read($buffer, 0, $bufferSize)
        if ($bytesRead -eq 0) {{ break }}
        
        $destStream.Write($buffer, 0, $bytesRead)
        $totalBytes += $bytesRead
        
        if ($totalBytes % 104857600 -eq 0) {{  # Every 100MB
            $mb = [math]::Round($totalBytes / 1048576, 1)
            $percent = [math]::Round(($totalBytes / $maxBytes) * 100, 1)
            Write-Host "[PS] Copied: ${{mb}}MB (${{percent}}%)"
        }}
    }}
    
    $sourceStream.Close()
    $destStream.Close()
    
    Write-Host "[PS] Precise copy completed. Total: $totalBytes bytes"
    Write-Host "SUCCESS:$totalBytes"
    
}} catch {{
    Write-Host "ERROR:$($_.Exception.Message)"
    exit 1
}}
'''
        
        try:
            result = subprocess.run([
                'powershell', '-ExecutionPolicy', 'Bypass', '-Command', ps_script
            ], capture_output=True, text=True, timeout=7200)  # 2 hour timeout
            
            print(f"[RESULT] PowerShell return code: {result.returncode}")
            
            if result.returncode == 0 and 'SUCCESS:' in result.stdout:
                for line in result.stdout.split('\n'):
                    if line.startswith('SUCCESS:'):
                        actual_copied = int(line.split(':')[1])
                        print(f"[SUCCESS] ✅ Precise clone completed: {actual_copied:,} bytes")
                        return True
            
            # Show error details
            print(f"[ERROR] Clone failed:")
            if result.stdout:
                print(f"STDOUT: {result.stdout}")
            if result.stderr:
                print(f"STDERR: {result.stderr}")
            return False
            
        except Exception as e:
            print(f"[ERROR] Exception during cloning: {e}")
            return False
    
    def create_precise_clone(self, source_drive: str) -> Optional[str]:
        """Create a precisely sized clone."""
        # Get actual drive size
        actual_size = self.get_actual_drive_size(source_drive)
        if not actual_size:
            print(f"[ERROR] Cannot determine drive size for {source_drive}")
            return None
        
        # Create output filename
        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        size_gb = int(actual_size / (1024**3))
        output_path = f"./sd_recovery/precise_clone_{size_gb}GB_{timestamp}.img"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create the precise clone
        if self.clone_precise_size(source_drive, output_path, actual_size):
            print(f"\n[COMPLETED] ✅ Precise clone created:")
            print(f"   File: {os.path.basename(output_path)}")
            print(f"   Size: {actual_size:,} bytes ({actual_size / (1024**3):.2f} GB)")
            return output_path
        else:
            print(f"\n[FAILED] ❌ Precise clone failed")
            return None

def main():
    import sys
    if len(sys.argv) != 2:
        print("Usage: python precise_clone.py <source_drive>")
        print("Example: python precise_clone.py \\\\.\\PhysicalDrive7")
        sys.exit(1)
    
    source_drive = sys.argv[1]
    cloner = PreciseCloner()
    
    print(f"🎯 PRECISE CLONING TOOL")
    print(f"Source: {source_drive}")
    
    result_path = cloner.create_precise_clone(source_drive)
    
    if result_path:
        print(f"\n[NEXT STEPS]")
        print(f"1. Test mount: python test_mount.py \"{result_path}\"")
        print(f"2. If mount fails, repair: python advanced_repair.py \"{result_path}\"")
    
    sys.exit(0 if result_path else 1)

if __name__ == "__main__":
    main()
