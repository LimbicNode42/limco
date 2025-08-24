#!/usr/bin/env python3
"""
Quick Clone Test - Test the fixed cloning without full recovery process
"""
import sys
import os
sys.path.append('.')
from cli_recovery import CLIDriveRecovery

def test_clone_only(source_drive: str):
    """Test just the cloning functionality with size limits."""
    print(f"🧪 TESTING SIZE-LIMITED CLONING")
    print(f"Source: {source_drive}")
    
    recovery = CLIDriveRecovery()
    
    # Create output path
    import time
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    clone_path = f"./test_recovery/size_limited_clone_{timestamp}.img"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(clone_path), exist_ok=True)
    
    print(f"Target: {clone_path}")
    print(f"Starting size-limited clone...")
    
    # Test the cloning
    result = recovery.create_recovery_clone(source_drive, os.path.dirname(clone_path), 
                                           clone_name=os.path.basename(clone_path).replace('.img', ''))
    
    if result['success']:
        clone_size = result.get('total_bytes', 0)
        clone_gb = clone_size / (1024**3)
        
        print(f"\n✅ SUCCESS!")
        print(f"Clone created: {os.path.basename(clone_path)}")
        print(f"Size: {clone_size:,} bytes ({clone_gb:.2f} GB)")
        print(f"Method: {result.get('method_used', 'unknown')}")
        
        # Check if size is reasonable (should be ~119GB, not 384GB)
        if clone_gb < 150:  # Less than 150GB
            print(f"✅ Size looks correct! (Expected ~119GB)")
            return True
        else:
            print(f"❌ Size still too large! (Expected ~119GB)")
            return False
    else:
        print(f"\n❌ FAILED!")
        print(f"Error: {result.get('error', 'Unknown error')}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_clone_only.py <source_drive>")
        print("Example: python test_clone_only.py \\\\.\\PhysicalDrive7")
        sys.exit(1)
    
    source_drive = sys.argv[1]
    success = test_clone_only(source_drive)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
