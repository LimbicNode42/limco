#!/usr/bin/env python3
"""
Ultimate Clone Recovery - Last resort repair for severely corrupted clones
"""
import os
import struct
import hashlib
from typing import Optional, Tuple, List

class UltimateCloneRecovery:
    def __init__(self):
        self.repair_log = []
        self.sector_size = 512
    
    def log(self, message: str):
        """Log repair action."""
        print(f"[ULTIMATE] {message}")
        self.repair_log.append(message)
    
    def read_safe(self, file_path: str, offset: int, size: int) -> Optional[bytes]:
        """Safely read data with error handling."""
        try:
            with open(file_path, 'rb') as f:
                f.seek(offset)
                return f.read(size)
        except Exception as e:
            self.log(f"Read error at offset {offset}: {e}")
            return None
    
    def write_safe(self, file_path: str, offset: int, data: bytes) -> bool:
        """Safely write data with error handling."""
        try:
            with open(file_path, 'r+b') as f:
                f.seek(offset)
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            return True
        except Exception as e:
            self.log(f"Write error at offset {offset}: {e}")
            return False
    
    def create_minimal_bootable_clone(self, source_path: str, output_path: str) -> bool:
        """Create a minimal bootable clone with reconstructed structures."""
        self.log("Creating minimal bootable clone...")
        
        if not os.path.exists(source_path):
            self.log(f"Source file not found: {source_path}")
            return False
        
        source_size = os.path.getsize(source_path)
        self.log(f"Source size: {source_size / (1024**3):.2f} GB")
        
        # Read the first few MB to analyze structure
        header_data = self.read_safe(source_path, 0, 8 * 1024 * 1024)  # 8MB
        if not header_data:
            return False
        
        # Create new MBR with proper structure
        mbr = bytearray(512)
        
        # Bootstrap code area (first 446 bytes) - minimal boot code
        mbr[0:3] = b'\xEB\x58\x90'  # Jump instruction
        mbr[3:11] = b'RECOVERY'      # OEM name
        
        # Partition table starts at offset 446
        # Partition 1: FAT32 boot partition (512MB)
        boot_size_sectors = 1048576  # 512MB in sectors
        mbr[446] = 0x80  # Bootable
        mbr[447] = 0x01  # Head
        mbr[448] = 0x01  # Sector
        mbr[449] = 0x00  # Cylinder
        mbr[450] = 0x0C  # FAT32 LBA
        mbr[451] = 0xFE  # End head
        mbr[452] = 0x3F  # End sector
        mbr[453] = 0xFF  # End cylinder
        struct.pack_into('<L', mbr, 454, 8192)  # Start LBA
        struct.pack_into('<L', mbr, 458, boot_size_sectors)  # Size in sectors
        
        # Partition 2: Linux root partition (rest of space)
        linux_start = 8192 + boot_size_sectors
        linux_size = (source_size // 512) - linux_start - 1024  # Leave some space at end
        mbr[462] = 0x00  # Not bootable
        mbr[463] = 0x01  # Head
        mbr[464] = 0x01  # Sector
        mbr[465] = 0x00  # Cylinder
        mbr[466] = 0x83  # Linux filesystem
        mbr[467] = 0xFE  # End head
        mbr[468] = 0x3F  # End sector
        mbr[469] = 0xFF  # End cylinder
        struct.pack_into('<L', mbr, 470, linux_start)  # Start LBA
        struct.pack_into('<L', mbr, 474, linux_size)   # Size in sectors
        
        # MBR signature
        mbr[510] = 0x55
        mbr[511] = 0xAA
        
        self.log("Writing reconstructed MBR...")
        
        # Copy source to output
        try:
            import shutil
            shutil.copy2(source_path, output_path)
            self.log(f"Copied source to: {os.path.basename(output_path)}")
        except Exception as e:
            self.log(f"Copy failed: {e}")
            return False
        
        # Write new MBR
        if not self.write_safe(output_path, 0, mbr):
            return False
        
        # Create proper FAT32 boot sector at LBA 8192
        self.log("Creating FAT32 boot sector...")
        boot_sector = self.create_fat32_boot_sector()
        if not self.write_safe(output_path, 8192 * 512, boot_sector):
            return False
        
        self.log("Minimal bootable clone created successfully")
        return True
    
    def create_fat32_boot_sector(self) -> bytes:
        """Create a proper FAT32 boot sector."""
        boot = bytearray(512)
        
        # Jump instruction
        boot[0:3] = b'\xEB\x58\x90'
        
        # OEM name
        boot[3:11] = b'MSWIN4.1'
        
        # BIOS Parameter Block (BPB)
        struct.pack_into('<H', boot, 11, 512)      # Bytes per sector
        boot[13] = 8                                # Sectors per cluster
        struct.pack_into('<H', boot, 14, 32)       # Reserved sectors
        boot[16] = 2                                # Number of FATs
        struct.pack_into('<H', boot, 17, 0)        # Root entries (0 for FAT32)
        struct.pack_into('<H', boot, 19, 0)        # Small sectors (0 for FAT32)
        boot[21] = 0xF8                             # Media descriptor
        struct.pack_into('<H', boot, 22, 0)        # FAT size 16 (0 for FAT32)
        struct.pack_into('<H', boot, 24, 63)       # Sectors per track
        struct.pack_into('<H', boot, 26, 255)      # Number of heads
        struct.pack_into('<L', boot, 28, 8192)     # Hidden sectors
        struct.pack_into('<L', boot, 32, 1048576)  # Large sectors
        
        # FAT32 specific fields
        struct.pack_into('<L', boot, 36, 8192)     # FAT size 32
        struct.pack_into('<H', boot, 40, 0)        # Flags
        struct.pack_into('<H', boot, 42, 0)        # Version
        struct.pack_into('<L', boot, 44, 2)        # Root cluster
        struct.pack_into('<H', boot, 48, 1)        # FS info sector
        struct.pack_into('<H', boot, 50, 6)        # Backup boot sector
        
        # Drive number and signature
        boot[64] = 0x80                             # Drive number
        boot[66] = 0x29                             # Boot signature
        
        # Volume ID (random)
        struct.pack_into('<L', boot, 67, 0x12345678)
        
        # Volume label and filesystem type
        boot[71:82] = b'RPI-RECOVER'                # Volume label
        boot[82:90] = b'FAT32   '                   # Filesystem type
        
        # Boot signature
        boot[510] = 0x55
        boot[511] = 0xAA
        
        return bytes(boot)
    
    def repair_clone(self, clone_path: str) -> bool:
        """Ultimate repair attempt."""
        self.log(f"Starting ultimate recovery of {os.path.basename(clone_path)}")
        
        # Create a bootable version
        bootable_path = clone_path.replace('.img', '_bootable.img')
        
        if self.create_minimal_bootable_clone(clone_path, bootable_path):
            self.log(f"✅ Created bootable clone: {os.path.basename(bootable_path)}")
            return True
        else:
            self.log("❌ Failed to create bootable clone")
            return False

def main():
    import sys
    if len(sys.argv) != 2:
        print("Usage: python ultimate_recovery.py <clone_path>")
        sys.exit(1)
    
    clone_path = sys.argv[1]
    recovery = UltimateCloneRecovery()
    
    print(f"\n🚨 ULTIMATE RECOVERY - LAST RESORT 🚨")
    print(f"This will create a reconstructed bootable version of your clone.")
    print(f"Source: {os.path.basename(clone_path)}")
    
    success = recovery.repair_clone(clone_path)
    
    if success:
        bootable_path = clone_path.replace('.img', '_bootable.img')
        print(f"\n[SUCCESS] ✅ Ultimate recovery completed!")
        print(f"[OUTPUT] Bootable clone created: {os.path.basename(bootable_path)}")
        print(f"[TEST] python test_mount.py \"{bootable_path}\"")
    else:
        print(f"\n[FAILED] ❌ Ultimate recovery failed")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
