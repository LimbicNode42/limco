#!/usr/bin/env python3
"""
Advanced Clone Repair Tool - Deep filesystem repair for corrupted clones
"""
import os
import struct
import shutil
from typing import Optional, Tuple, List

class AdvancedCloneRepairer:
    def __init__(self):
        self.repair_log = []
    
    def log_repair(self, message: str):
        """Log repair action."""
        print(f"[REPAIR] {message}")
        self.repair_log.append(message)
    
    def read_sectors(self, file_path: str, start_sector: int, count: int = 1) -> Optional[bytes]:
        """Read sectors from clone file."""
        try:
            with open(file_path, 'rb') as f:
                f.seek(start_sector * 512)
                return f.read(count * 512)
        except Exception as e:
            print(f"[ERROR] Failed to read sector {start_sector}: {e}")
            return None
    
    def write_sectors(self, file_path: str, start_sector: int, data: bytes) -> bool:
        """Write sectors to clone file."""
        try:
            with open(file_path, 'r+b') as f:
                f.seek(start_sector * 512)
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            return True
        except Exception as e:
            print(f"[ERROR] Failed to write sector {start_sector}: {e}")
            return False
    
    def repair_mbr(self, file_path: str) -> bool:
        """Repair Master Boot Record."""
        self.log_repair("Checking MBR...")
        
        mbr_data = self.read_sectors(file_path, 0, 1)
        if not mbr_data:
            return False
        
        repairs_made = False
        mbr = bytearray(mbr_data)
        
        # Check MBR signature
        if mbr[510] != 0x55 or mbr[511] != 0xAA:
            self.log_repair("Fixing MBR signature")
            mbr[510] = 0x55
            mbr[511] = 0xAA
            repairs_made = True
        
        # Check partition table (starts at offset 446)
        partition_table_start = 446
        for i in range(4):  # 4 partition entries
            offset = partition_table_start + (i * 16)
            
            # Get partition type
            part_type = mbr[offset + 4]
            if part_type == 0:
                continue  # Empty partition
            
            # Check for common Raspberry Pi partition types
            if part_type == 0x0B or part_type == 0x0C:  # FAT32
                self.log_repair(f"Found FAT32 partition {i+1}")
                # Ensure it's marked as bootable if it's the first partition
                if i == 0 and mbr[offset] != 0x80:
                    self.log_repair(f"Making partition {i+1} bootable")
                    mbr[offset] = 0x80
                    repairs_made = True
            elif part_type == 0x83:  # Linux ext2/3/4
                self.log_repair(f"Found Linux partition {i+1}")
        
        if repairs_made:
            if self.write_sectors(file_path, 0, mbr):
                self.log_repair("MBR repairs written successfully")
                return True
            else:
                self.log_repair("Failed to write MBR repairs")
                return False
        else:
            self.log_repair("MBR appears healthy")
            return True
    
    def repair_fat32_boot_sector(self, file_path: str, partition_start: int) -> bool:
        """Repair FAT32 boot sector."""
        self.log_repair(f"Repairing FAT32 boot sector at LBA {partition_start}")
        
        boot_data = self.read_sectors(file_path, partition_start, 1)
        if not boot_data:
            return False
        
        boot = bytearray(boot_data)
        repairs_made = False
        
        # Check jump instruction (should be EB xx 90 or E9 xx xx)
        if boot[0] not in [0xEB, 0xE9]:
            self.log_repair("Fixing jump instruction")
            boot[0] = 0xEB
            boot[1] = 0x58  # Common offset
            boot[2] = 0x90
            repairs_made = True
        
        # Fix OEM name if corrupted
        oem_name = boot[3:11]
        if b'\x00' in oem_name or not all(32 <= b <= 126 for b in oem_name):
            self.log_repair("Fixing OEM name")
            boot[3:11] = b'MSWIN4.1'
            repairs_made = True
        
        # Check bytes per sector (should be 512)
        bytes_per_sector = struct.unpack('<H', boot[11:13])[0]
        if bytes_per_sector != 512:
            self.log_repair(f"Fixing bytes per sector: {bytes_per_sector} -> 512")
            boot[11:13] = struct.pack('<H', 512)
            repairs_made = True
        
        # Check sectors per cluster (common values: 1, 2, 4, 8, 16, 32, 64, 128)
        sectors_per_cluster = boot[13]
        if sectors_per_cluster not in [1, 2, 4, 8, 16, 32, 64, 128]:
            self.log_repair(f"Fixing sectors per cluster: {sectors_per_cluster} -> 8")
            boot[13] = 8
            repairs_made = True
        
        # Check media descriptor (should be F8 for hard disk)
        if boot[21] != 0xF8:
            self.log_repair("Fixing media descriptor")
            boot[21] = 0xF8
            repairs_made = True
        
        # Check boot signature
        if boot[510] != 0x55 or boot[511] != 0xAA:
            self.log_repair("Fixing boot sector signature")
            boot[510] = 0x55
            boot[511] = 0xAA
            repairs_made = True
        
        # Fix filesystem type identifier
        fs_type = boot[82:90]
        if fs_type != b'FAT32   ':
            self.log_repair("Fixing filesystem type identifier")
            boot[82:90] = b'FAT32   '
            repairs_made = True
        
        if repairs_made:
            if self.write_sectors(file_path, partition_start, boot):
                self.log_repair("FAT32 boot sector repairs written successfully")
                return True
            else:
                self.log_repair("Failed to write FAT32 boot sector repairs")
                return False
        else:
            self.log_repair("FAT32 boot sector appears healthy")
            return True
    
    def create_backup_and_repair(self, clone_path: str) -> bool:
        """Create backup and perform comprehensive repair."""
        print(f"\n[ADVANCED REPAIR] Starting comprehensive repair of {os.path.basename(clone_path)}")
        
        if not os.path.exists(clone_path):
            print(f"[ERROR] Clone file not found: {clone_path}")
            return False
        
        # Create backup
        backup_path = clone_path + ".backup"
        if not os.path.exists(backup_path):
            print(f"[BACKUP] Creating backup: {os.path.basename(backup_path)}")
            try:
                shutil.copy2(clone_path, backup_path)
                print(f"[BACKUP] Backup created successfully")
            except Exception as e:
                print(f"[ERROR] Failed to create backup: {e}")
                return False
        else:
            print(f"[BACKUP] Using existing backup: {os.path.basename(backup_path)}")
        
        # Read MBR to find partitions
        print(f"[ANALYZE] Analyzing partition structure...")
        mbr_data = self.read_sectors(clone_path, 0, 1)
        if not mbr_data:
            return False
        
        # Parse partition table
        partitions = []
        for i in range(4):
            offset = 446 + (i * 16)
            part_type = mbr_data[offset + 4]
            if part_type != 0:
                start_lba = struct.unpack('<L', mbr_data[offset + 8:offset + 12])[0]
                size_sectors = struct.unpack('<L', mbr_data[offset + 12:offset + 16])[0]
                partitions.append((i, part_type, start_lba, size_sectors))
                print(f"[PARTITION] {i+1}: Type=0x{part_type:02X}, Start={start_lba}, Size={size_sectors}")
        
        # Perform repairs
        success = True
        
        # 1. Repair MBR
        if not self.repair_mbr(clone_path):
            success = False
        
        # 2. Repair each partition
        for part_num, part_type, start_lba, size_sectors in partitions:
            if part_type in [0x0B, 0x0C]:  # FAT32
                if not self.repair_fat32_boot_sector(clone_path, start_lba):
                    success = False
            elif part_type == 0x83:  # Linux
                self.log_repair(f"Linux partition {part_num+1} - basic validation only")
        
        print(f"\n[SUMMARY] Repair Summary:")
        for repair in self.repair_log:
            print(f"  ✓ {repair}")
        
        return success

def main():
    import sys
    if len(sys.argv) != 2:
        print("Usage: python advanced_repair.py <clone_path>")
        sys.exit(1)
    
    clone_path = sys.argv[1]
    repairer = AdvancedCloneRepairer()
    
    success = repairer.create_backup_and_repair(clone_path)
    
    if success:
        print(f"\n[SUCCESS] ✅ Advanced repair completed!")
        print(f"[NEXT] Test mounting with: python test_mount.py \"{clone_path}\"")
    else:
        print(f"\n[FAILED] ❌ Some repairs failed - check logs above")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
