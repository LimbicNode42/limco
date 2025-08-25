#!/usr/bin/env python3
"""
SD Card Size Fixer - Create a clone that exactly fits on your SD card
"""
import os
import sys

def trim_clone_to_sd_size(clone_path: str, target_size_gb: int = 119) -> str:
    """Trim clone to exactly fit SD card size."""
    print(f"🔧 TRIMMING CLONE TO SD CARD SIZE")
    print(f"Source: {os.path.basename(clone_path)}")
    print(f"Target size: {target_size_gb} GB")
    
    if not os.path.exists(clone_path):
        print(f"❌ Clone file not found: {clone_path}")
        return None
    
    current_size = os.path.getsize(clone_path)
    current_gb = current_size / (1024**3)
    target_size_bytes = target_size_gb * (1024**3)
    
    print(f"Current size: {current_gb:.2f} GB ({current_size:,} bytes)")
    print(f"Target size:  {target_size_gb} GB ({target_size_bytes:,} bytes)")
    
    if current_size <= target_size_bytes:
        print(f"✅ Clone is already small enough!")
        return clone_path
    
    # Create trimmed version
    trimmed_path = clone_path.replace('.img', '_trimmed.img')
    
    print(f"Creating trimmed clone: {os.path.basename(trimmed_path)}")
    
    try:
        with open(clone_path, 'rb') as source:
            with open(trimmed_path, 'wb') as target:
                # Copy in 10MB chunks
                chunk_size = 10 * 1024 * 1024
                copied = 0
                
                while copied < target_size_bytes:
                    remaining = target_size_bytes - copied
                    read_size = min(chunk_size, remaining)
                    
                    chunk = source.read(read_size)
                    if not chunk:
                        break
                    
                    target.write(chunk)
                    copied += len(chunk)
                    
                    if copied % (100 * 1024 * 1024) == 0:  # Every 100MB
                        progress = (copied / target_size_bytes) * 100
                        print(f"Progress: {progress:.1f}% ({copied / (1024**3):.1f} GB)")
        
        final_size = os.path.getsize(trimmed_path)
        final_gb = final_size / (1024**3)
        
        print(f"✅ Trimmed clone created!")
        print(f"Final size: {final_gb:.2f} GB ({final_size:,} bytes)")
        print(f"Savings: {current_gb - final_gb:.2f} GB")
        
        return trimmed_path
        
    except Exception as e:
        print(f"❌ Failed to create trimmed clone: {e}")
        return None

def get_actual_partition_size(clone_path: str) -> int:
    """Get the actual size needed based on partition table."""
    try:
        with open(clone_path, 'rb') as f:
            # Read MBR
            mbr = f.read(512)
            
            max_end_sector = 0
            partition_count = 0
            
            # Check all 4 primary partitions
            for i in range(4):
                offset = 446 + (i * 16)
                part_type = mbr[offset + 4]
                
                if part_type != 0:  # Active partition
                    import struct
                    start_lba = struct.unpack('<L', mbr[offset + 8:offset + 12])[0]
                    size_sectors = struct.unpack('<L', mbr[offset + 12:offset + 16])[0]
                    end_sector = start_lba + size_sectors
                    
                    print(f"Partition {i+1}: Type=0x{part_type:02X}, Start={start_lba}, Size={size_sectors} sectors")
                    print(f"   Size: {(size_sectors * 512) / (1024**3):.2f} GB")
                    
                    max_end_sector = max(max_end_sector, end_sector)
                    partition_count += 1
            
            if max_end_sector > 0:
                actual_size_bytes = max_end_sector * 512
                actual_size_gb = actual_size_bytes / (1024**3)
                
                print(f"\nActual data ends at sector {max_end_sector}")
                print(f"Actual size needed: {actual_size_gb:.2f} GB ({actual_size_bytes:,} bytes)")
                
                return actual_size_bytes
            else:
                print("No valid partitions found")
                return None
                
    except Exception as e:
        print(f"Error reading partition table: {e}")
        return None

def main():
    if len(sys.argv) not in [2, 3]:
        print("Usage: python sd_size_fixer.py <clone_path> [target_gb]")
        print("Example: python sd_size_fixer.py ./sd_recovery/recovery_clone.img 119")
        sys.exit(1)
    
    clone_path = sys.argv[1]
    target_gb = int(sys.argv[2]) if len(sys.argv) > 2 else 119
    
    print("📊 Analyzing partition structure...")
    actual_size = get_actual_partition_size(clone_path)
    
    if actual_size:
        actual_gb = actual_size / (1024**3)
        if actual_gb < target_gb:
            print(f"\n💡 Suggestion: You only need {actual_gb:.0f}GB based on partition table")
            target_gb = min(target_gb, int(actual_gb) + 1)  # Add 1GB buffer
    
    result = trim_clone_to_sd_size(clone_path, target_gb)
    
    if result:
        print(f"\n🎉 SUCCESS!")
        print(f"SD-compatible clone: {os.path.basename(result)}")
        print(f"Ready to flash to your {target_gb}GB+ SD card!")
    else:
        print(f"\n❌ FAILED to create SD-compatible clone")

if __name__ == "__main__":
    main()
