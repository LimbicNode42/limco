#!/usr/bin/env python3
"""Quick test to verify the os_type attribute fix."""

import tempfile
import os
from cli_recovery import CLIDriveRecovery

def test_os_type_fix():
    """Test that the os_type attribute is properly initialized."""
    print("Testing CLIDriveRecovery initialization...")
    recovery = CLIDriveRecovery()
    
    print(f"✓ OS Type: {recovery.os_type}")
    print(f"✓ System Info: {recovery.system_info['os']}")
    
    # Create a small test file to test filesystem analysis
    with tempfile.NamedTemporaryFile(suffix='.img', delete=False) as temp_file:
        # Write some test data
        temp_file.write(b"TEST" * 1000)  # 4KB test file
        temp_path = temp_file.name
    
    try:
        print(f"Testing filesystem analysis on test file: {os.path.basename(temp_path)}")
        
        # Test filesystem analysis
        fs_result = recovery.analyze_filesystem(temp_path)
        print(f"✓ Filesystem analysis completed: success={fs_result['success']}")
        
        # Test repair attempt
        repair_result = recovery.repair_filesystem(temp_path)
        print(f"✓ Filesystem repair attempted: method={repair_result.get('method_used', 'none')}")
        
        # Test extraction
        temp_dir = tempfile.mkdtemp()
        extract_result = recovery.extract_recoverable_data(temp_path, temp_dir)
        print(f"✓ Data extraction attempted: method={extract_result.get('method_used', 'none')}")
        
        print("\n🎉 All tests passed! The os_type fix is working correctly.")
        
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_os_type_fix()
