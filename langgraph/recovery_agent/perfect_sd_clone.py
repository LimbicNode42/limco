#!/usr/bin/env python3
"""
Perfect SD Clone - Create a clone that exactly fits your SD card
"""
import subprocess
import os
import time

def create_perfect_sd_clone(source_drive: str, max_size_gb: int = 119):
    """Create a clone that fits perfectly on SD card."""
    print(f"🎯 CREATING PERFECT SD CLONE")
    print(f"Source: {source_drive}")
    print(f"Max size: {max_size_gb} GB")
    
    # Extract disk number
    if 'PhysicalDrive' not in source_drive:
        print(f"❌ Invalid drive path: {source_drive}")
        return None
    
    disk_num = source_drive.split('PhysicalDrive')[1]
    max_size_bytes = max_size_gb * (1024**3)
    
    # Create output path
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = f"./sd_recovery/perfect_sd_clone_{max_size_gb}GB_{timestamp}.img"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"Output: {output_path}")
    print(f"Size limit: {max_size_bytes:,} bytes ({max_size_gb} GB)")
    
    # PowerShell script with strict size limit
    ps_script = f'''
try {{
    $sourcePath = "{source_drive}"
    $destPath = "{output_path}"
    $maxBytes = {max_size_bytes}
    
    Write-Host "[PS] Opening source: $sourcePath"
    Write-Host "[PS] Max size limit: $maxBytes bytes ({max_size_gb} GB)"
    
    $sourceStream = [System.IO.File]::OpenRead($sourcePath)
    $destStream = [System.IO.File]::Create($destPath)
    
    Write-Host "[PS] Starting perfect-size copy..."
    $buffer = New-Object byte[] 4194304  # 4MB buffer
    $totalBytes = 0
    $lastProgressMB = 0
    
    while ($totalBytes -lt $maxBytes) {{
        $remainingBytes = $maxBytes - $totalBytes
        $bufferSize = [Math]::Min($buffer.Length, $remainingBytes)
        
        try {{
            $bytesRead = $sourceStream.Read($buffer, 0, $bufferSize)
            if ($bytesRead -eq 0) {{
                Write-Host "[PS] Reached end of readable data at $totalBytes bytes"
                break
            }}
            
            $destStream.Write($buffer, 0, $bytesRead)
            $totalBytes += $bytesRead
            
            # Progress every 100MB
            $currentMB = [math]::Floor($totalBytes / 1048576)
            if ($currentMB -ge $lastProgressMB + 100) {{
                $percent = [math]::Round(($totalBytes / $maxBytes) * 100, 1)
                $gb = [math]::Round($totalBytes / 1073741824, 2)
                Write-Host "[PS] Progress: ${{gb}} GB (${{percent}}%)"
                $lastProgressMB = $currentMB
            }}
            
            # Stop exactly at size limit
            if ($totalBytes -ge $maxBytes) {{
                Write-Host "[PS] Reached perfect size limit: $totalBytes bytes"
                break
            }}
            
        }} catch {{
            Write-Host "[PS] Read error at $totalBytes bytes: $($_.Exception.Message)"
            
            # If we're close to the limit, stop rather than skip
            if ($totalBytes -ge ($maxBytes * 0.95)) {{
                Write-Host "[PS] Near size limit with error, stopping"
                break
            }}
            
            # Try to skip bad area
            try {{
                $skipSize = [Math]::Min($bufferSize, $maxBytes - $totalBytes)
                $sourceStream.Seek($totalBytes + $skipSize, [System.IO.SeekOrigin]::Begin) | Out-Null
                # Fill with zeros
                $zeroBuffer = New-Object byte[] $skipSize
                $destStream.Write($zeroBuffer, 0, $skipSize)
                $totalBytes += $skipSize
                Write-Host "[PS] Skipped bad sector, continuing..."
            }} catch {{
                Write-Host "[PS] Cannot skip, stopping"
                break
            }}
        }}
    }}
    
    $sourceStream.Close()
    $destStream.Close()
    
    Write-Host "[PS] Perfect clone completed!"
    Write-Host "[PS] Final size: $totalBytes bytes"
    Write-Host "[PS] Size check: $(if ($totalBytes -le $maxBytes) {{"PERFECT"}} else {{"OVERSIZED"}})"
    Write-Host "SUCCESS:$totalBytes"
    
}} catch {{
    Write-Host "ERROR:$($_.Exception.Message)"
    exit 1
}}
'''
    
    print(f"\n🚀 Starting perfect clone creation...")
    
    try:
        result = subprocess.run([
            'powershell', '-ExecutionPolicy', 'Bypass', '-Command', ps_script
        ], capture_output=True, text=True, timeout=7200)  # 2 hour timeout
        
        print(f"PowerShell result: {result.returncode}")
        
        if result.returncode == 0 and 'SUCCESS:' in result.stdout:
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(f"[PS] {line.strip()}")
                if line.startswith('SUCCESS:'):
                    final_bytes = int(line.split(':')[1])
                    final_gb = final_bytes / (1024**3)
                    
                    print(f"\n✅ PERFECT SD CLONE CREATED!")
                    print(f"File: {os.path.basename(output_path)}")
                    print(f"Size: {final_gb:.2f} GB ({final_bytes:,} bytes)")
                    print(f"Will fit on SD: {'YES' if final_bytes <= max_size_bytes else 'NO'}")
                    
                    return output_path
        else:
            print(f"❌ Clone creation failed:")
            if result.stdout:
                print(f"STDOUT: {result.stdout}")
            if result.stderr:
                print(f"STDERR: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Exception during cloning: {e}")
        return None

def main():
    import sys
    if len(sys.argv) not in [2, 3]:
        print("Usage: python perfect_sd_clone.py <source_drive> [max_gb]")
        print("Example: python perfect_sd_clone.py \\\\.\\PhysicalDrive6 119")
        sys.exit(1)
    
    source_drive = sys.argv[1]
    max_gb = int(sys.argv[2]) if len(sys.argv) > 2 else 119
    
    result = create_perfect_sd_clone(source_drive, max_gb)
    
    if result:
        print(f"\n🎉 Ready to flash to SD card!")
        print(f"Clone: {result}")
        print(f"\n📝 Next steps:")
        print(f"1. Use Win32DiskImager, Rufus, or dd to flash {os.path.basename(result)} to your SD card")
        print(f"2. The clone is guaranteed to fit on any {max_gb}GB+ SD card")
    else:
        print(f"\n❌ Failed to create perfect SD clone")
    
    sys.exit(0 if result else 1)

if __name__ == "__main__":
    main()
