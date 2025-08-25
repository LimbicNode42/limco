#!/usr/bin/env python3
"""
MBR Fixer - Repair Master Boot Record corruption for Raspberry Pi SD cards
"""
import os
import struct
from typing import Dict, Any

class MBRFixer:
    def __init__(self):
        self.sector_size = 512
    
    def analyze_mbr(self, clone_path: str) -> Dict[str, Any]:
        """Analyze the current MBR structure."""
        print(f"🔍 ANALYZING MBR: {os.path.basename(clone_path)}")
        
        if not os.path.exists(clone_path):
            return {'error': 'File not found'}
        
        try:
            with open(clone_path, 'rb') as f:
                mbr_data = f.read(512)
                
                analysis = {
                    'mbr_size': len(mbr_data),
                    'boot_signature': (mbr_data[510], mbr_data[511]),
                    'boot_signature_valid': mbr_data[510] == 0x55 and mbr_data[511] == 0xAA,
                    'partitions': [],
                    'issues': []
                }
                
                print(f"MBR Size: {analysis['mbr_size']} bytes")
                print(f"Boot Signature: {analysis['boot_signature']} (should be (85, 170))")
                print(f"Boot Signature Valid: {analysis['boot_signature_valid']}")
                
                if not analysis['boot_signature_valid']:
                    analysis['issues'].append('Invalid boot signature')
                
                # Check bootstrap code area (first 446 bytes)
                bootstrap = mbr_data[:446]
                zero_count = bootstrap.count(0)
                print(f"Bootstrap area: {zero_count}/446 bytes are zero")
                
                if zero_count > 400:  # More than 90% zeros
                    analysis['issues'].append('Bootstrap code area mostly empty')
                
                # Parse partition table
                print(f"\nPartition Table:")
                for i in range(4):
                    offset = 446 + (i * 16)
                    part_data = mbr_data[offset:offset + 16]
                    
                    if len(part_data) < 16:
                        continue
                    
                    bootable = part_data[0]
                    part_type = part_data[4]
                    start_lba = struct.unpack('<L', part_data[8:12])[0]
                    size_sectors = struct.unpack('<L', part_data[12:16])[0]
                    
                    partition = {
                        'number': i + 1,
                        'bootable': bootable,
                        'type': part_type,
                        'start_lba': start_lba,
                        'size_sectors': size_sectors,
                        'size_mb': (size_sectors * 512) / (1024**2),
                        'valid': part_type != 0
                    }
                    
                    analysis['partitions'].append(partition)
                    
                    if partition['valid']:
                        bootable_text = "Yes" if bootable == 0x80 else "No"
                        print(f"  Partition {i+1}: Type=0x{part_type:02X}, Bootable={bootable_text}, Start={start_lba}, Size={partition['size_mb']:.1f}MB")
                        
                        # Validate partition
                        if start_lba == 0:
                            analysis['issues'].append(f'Partition {i+1} has invalid start sector 0')
                        if size_sectors == 0:
                            analysis['issues'].append(f'Partition {i+1} has zero size')
                
                # Check for Raspberry Pi specific issues
                valid_partitions = [p for p in analysis['partitions'] if p['valid']]
                if len(valid_partitions) < 2:
                    analysis['issues'].append('Expected 2 partitions for Raspberry Pi (boot + root)')
                
                # Check if first partition is FAT32 and bootable
                if valid_partitions:
                    first_part = valid_partitions[0]
                    if first_part['type'] not in [0x0B, 0x0C]:  # FAT32
                        analysis['issues'].append('First partition should be FAT32 for Raspberry Pi')
                    if first_part['bootable'] != 0x80:
                        analysis['issues'].append('First partition should be bootable for Raspberry Pi')
                
                return analysis
                
        except Exception as e:
            return {'error': f'Failed to analyze MBR: {e}'}
    
    def create_raspberry_pi_mbr(self) -> bytes:
        """Create a proper Raspberry Pi MBR."""
        mbr = bytearray(512)
        
        # Bootstrap code - minimal for Raspberry Pi
        mbr[0:3] = b'\xEB\x58\x90'  # Jump instruction
        mbr[3:11] = b'RPI-BOOT'      # OEM identifier
        
        # Partition 1: FAT32 Boot partition (512MB)
        # Starts at LBA 8192 (4MB offset - common for Raspberry Pi)
        offset1 = 446
        mbr[offset1] = 0x80         # Bootable
        mbr[offset1 + 1] = 0x01     # Start head
        mbr[offset1 + 2] = 0x01     # Start sector
        mbr[offset1 + 3] = 0x00     # Start cylinder
        mbr[offset1 + 4] = 0x0C     # FAT32 LBA
        mbr[offset1 + 5] = 0xFE     # End head
        mbr[offset1 + 6] = 0x3F     # End sector
        mbr[offset1 + 7] = 0xFF     # End cylinder
        struct.pack_into('<L', mbr, offset1 + 8, 8192)      # Start LBA
        struct.pack_into('<L', mbr, offset1 + 12, 1048576)  # Size (512MB)
        
        # Partition 2: Linux root partition (rest of space)
        # Calculate size based on total disk size minus boot partition and some reserved space
        root_start = 8192 + 1048576  # After boot partition
        root_size = 249290752        # Approximate remaining space (adjust based on actual disk)
        
        offset2 = 446 + 16
        mbr[offset2] = 0x00         # Not bootable
        mbr[offset2 + 1] = 0x01     # Start head
        mbr[offset2 + 2] = 0x01     # Start sector
        mbr[offset2 + 3] = 0x00     # Start cylinder
        mbr[offset2 + 4] = 0x83     # Linux filesystem
        mbr[offset2 + 5] = 0xFE     # End head
        mbr[offset2 + 6] = 0x3F     # End sector
        mbr[offset2 + 7] = 0xFF     # End cylinder
        struct.pack_into('<L', mbr, offset2 + 8, root_start)  # Start LBA
        struct.pack_into('<L', mbr, offset2 + 12, root_size)  # Size
        
        # Boot signature
        mbr[510] = 0x55
        mbr[511] = 0xAA
        
        return bytes(mbr)
    
    def fix_mbr(self, clone_path: str, create_backup: bool = True) -> bool:
        """Fix the MBR in the clone file."""
        print(f"\n🔧 FIXING MBR: {os.path.basename(clone_path)}")
        
        if create_backup:
            backup_path = clone_path + '.mbr_backup'
            try:
                # Backup original MBR
                with open(clone_path, 'rb') as src:
                    original_mbr = src.read(512)
                with open(backup_path, 'wb') as backup:
                    backup.write(original_mbr)
                print(f"✅ Created MBR backup: {os.path.basename(backup_path)}")
            except Exception as e:
                print(f"⚠️ Could not create backup: {e}")
        
        try:
            # Read current MBR to preserve partition information
            with open(clone_path, 'rb') as f:
                current_mbr = bytearray(f.read(512))
            
            # Create new MBR
            new_mbr = bytearray(self.create_raspberry_pi_mbr())
            
            # Try to preserve existing partition table if it looks valid
            try:
                # Check if existing partitions have reasonable values
                for i in range(4):
                    offset = 446 + (i * 16)
                    part_type = current_mbr[offset + 4]
                    start_lba = struct.unpack('<L', current_mbr[offset + 8:offset + 12])[0]
                    size_sectors = struct.unpack('<L', current_mbr[offset + 12:offset + 16])[0]
                    
                    if part_type != 0 and start_lba > 0 and size_sectors > 0:
                        print(f"Preserving partition {i+1}: type=0x{part_type:02X}, start={start_lba}, size={size_sectors}")
                        # Copy the partition entry
                        new_mbr[offset:offset + 16] = current_mbr[offset:offset + 16]
                        
                        # Ensure first partition is bootable
                        if i == 0:
                            new_mbr[offset] = 0x80
            
            except Exception as e:
                print(f"Using default partition table: {e}")
            
            # Write fixed MBR
            with open(clone_path, 'r+b') as f:
                f.seek(0)
                f.write(new_mbr)
                f.flush()
                os.fsync(f.fileno())
            
            print(f"✅ MBR fixed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to fix MBR: {e}")
            return False

def main():
    import sys
    if len(sys.argv) != 2:
        print("Usage: python mbr_fixer.py <clone_path>")
        sys.exit(1)
    
    clone_path = sys.argv[1]
    fixer = MBRFixer()
    
    # Analyze current MBR
    analysis = fixer.analyze_mbr(clone_path)
    
    if 'error' in analysis:
        print(f"❌ Error: {analysis['error']}")
        sys.exit(1)
    
    print(f"\n🔍 Issues found: {len(analysis['issues'])}")
    for issue in analysis['issues']:
        print(f"  ❌ {issue}")
    
    if analysis['issues']:
        print(f"\n🔧 Attempting to fix MBR...")
        if fixer.fix_mbr(clone_path):
            print(f"\n✅ MBR fixed! Try flashing again.")
            
            # Re-analyze to confirm fix
            print(f"\n🔍 Verifying fix...")
            new_analysis = fixer.analyze_mbr(clone_path)
            if new_analysis.get('boot_signature_valid', False):
                print(f"✅ Boot signature now valid!")
            else:
                print(f"❌ Boot signature still invalid")
        else:
            print(f"\n❌ MBR fix failed")
    else:
        print(f"\n✅ MBR looks good - the issue might be elsewhere")

if __name__ == "__main__":
    main()
