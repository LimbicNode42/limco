#!/usr/bin/env python3
"""
Test Drive Size Detection - Verify we can get accurate drive sizes
"""
import subprocess
import sys

def test_drive_size_detection(drive_path: str):
    """Test drive size detection methods."""
    print(f"🔍 Testing drive size detection for: {drive_path}")
    
    if 'PhysicalDrive' not in drive_path:
        print("❌ Not a physical drive path")
        return
    
    disk_num = drive_path.split('PhysicalDrive')[1]
    print(f"📀 Disk number: {disk_num}")
    
    # Method 1: PowerShell Get-Disk
    print(f"\n[METHOD 1] PowerShell Get-Disk")
    ps_script1 = f'''
try {{
    $disk = Get-Disk -Number {disk_num} -ErrorAction Stop
    Write-Host "SIZE:$($disk.Size)"
    Write-Host "MODEL:$($disk.FriendlyName)"
    Write-Host "STATUS:$($disk.OperationalStatus)"
}} catch {{
    Write-Host "ERROR:$($_.Exception.Message)"
}}
'''
    
    try:
        result1 = subprocess.run(['powershell', '-Command', ps_script1], 
                                capture_output=True, text=True, timeout=30)
        
        for line in result1.stdout.split('\n'):
            line = line.strip()
            if line.startswith('SIZE:'):
                size_bytes = int(line.split(':')[1].strip())
                size_gb = size_bytes / (1024**3)
                print(f"   ✅ Size: {size_bytes:,} bytes ({size_gb:.2f} GB)")
            elif line.startswith('MODEL:'):
                model = line.split(':', 1)[1].strip()
                print(f"   📱 Model: {model}")
            elif line.startswith('STATUS:'):
                status = line.split(':', 1)[1].strip()
                print(f"   📊 Status: {status}")
            elif line.startswith('ERROR:'):
                error = line.split(':', 1)[1].strip()
                print(f"   ❌ Error: {error}")
                
    except Exception as e:
        print(f"   ❌ Method 1 failed: {e}")
    
    # Method 2: WMI Win32_DiskDrive
    print(f"\n[METHOD 2] WMI Win32_DiskDrive")
    ps_script2 = f'''
try {{
    $disk = Get-WmiObject -Class Win32_DiskDrive | Where-Object {{ $_.DeviceID -eq "\\\\.\\PHYSICALDRIVE{disk_num}" }}
    if ($disk) {{
        Write-Host "SIZE:$($disk.Size)"
        Write-Host "MODEL:$($disk.Model)"
        Write-Host "MEDIA:$($disk.MediaType)"
    }} else {{
        Write-Host "ERROR:Disk not found"
    }}
}} catch {{
    Write-Host "ERROR:$($_.Exception.Message)"
}}
'''
    
    try:
        result2 = subprocess.run(['powershell', '-Command', ps_script2], 
                                capture_output=True, text=True, timeout=30)
        
        for line in result2.stdout.split('\n'):
            line = line.strip()
            if line.startswith('SIZE:'):
                size_bytes = int(line.split(':')[1].strip())
                size_gb = size_bytes / (1024**3)
                print(f"   ✅ Size: {size_bytes:,} bytes ({size_gb:.2f} GB)")
            elif line.startswith('MODEL:'):
                model = line.split(':', 1)[1].strip()
                print(f"   📱 Model: {model}")
            elif line.startswith('MEDIA:'):
                media = line.split(':', 1)[1].strip()
                print(f"   💿 Media: {media}")
            elif line.startswith('ERROR:'):
                error = line.split(':', 1)[1].strip()
                print(f"   ❌ Error: {error}")
                
    except Exception as e:
        print(f"   ❌ Method 2 failed: {e}")
    
    print(f"\n✅ Drive size detection test completed!")

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_drive_size.py <drive_path>")
        print("Example: python test_drive_size.py \\\\.\\PhysicalDrive7")
        sys.exit(1)
    
    drive_path = sys.argv[1]
    test_drive_size_detection(drive_path)

if __name__ == "__main__":
    main()
