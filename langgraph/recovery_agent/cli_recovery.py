#!/usr/bin/env python3
"""
Standalone CLI Drive Recovery Tool
No LangGraph, LangSmith, or Studio required - just pure Python!

Usage:
    python cli_recovery.py --scan-drives
    python cli_recovery.py --recover --source /dev/disk2 --output ./recovery
    python cli_recovery.py --analyze-only --source /dev/disk2
"""

import os
import sys
import json
import argparse
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add src to path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Try to import AI modules (optional)
ErrorRecoveryHandler = None
SelfImprovementEngine = None
DriveAnalyzer = None

try:
    from recovery_agent.self_improvement import ErrorRecoveryHandler, SelfImprovementEngine
    print("[OK] Self-improvement module loaded")
except ImportError as e:
    print(f"[WARN] Self-improvement module unavailable: {e}")

try:
    from recovery_agent.llm_analysis import RecoveryAnalystLLM
    DriveAnalyzer = RecoveryAnalystLLM  # Use alias for compatibility
    print("[OK] LLM analysis module loaded")
except ImportError as e:
    print(f"[WARN] LLM analysis module unavailable: {e}")
    DriveAnalyzer = None

if not (ErrorRecoveryHandler and DriveAnalyzer):
    print("[INFO] Running in basic mode without AI features")
    print("       Install requirements and set ANTHROPIC_API_KEY for full functionality")


class CLIDriveRecovery:
    """Standalone CLI Drive Recovery Tool"""
    
    def __init__(self):
        self.system_info = {
            'os': platform.system(),
            'platform': platform.platform(),
            'is_admin': self._check_admin_privileges()
        }
        self.error_handler = None
        self.drive_analyzer = None
        
        # Try to initialize AI components if available
        try:
            if ErrorRecoveryHandler and os.getenv('ANTHROPIC_API_KEY'):
                self.error_handler = ErrorRecoveryHandler()
                print("[AI] Error recovery enabled")
            else:
                print("[INFO] AI error recovery unavailable")
        except Exception as e:
            print(f"[WARN] Could not initialize error recovery: {e}")
        
        try:
            if DriveAnalyzer and os.getenv('ANTHROPIC_API_KEY'):
                self.drive_analyzer = DriveAnalyzer()
                print("[AI] Drive analysis enabled")
            else:
                print("[INFO] AI drive analysis unavailable")
        except Exception as e:
            print(f"[WARN] Could not initialize drive analyzer: {e}")
        
        if not (self.error_handler or self.drive_analyzer):
            print("[INFO] Running in basic mode (set ANTHROPIC_API_KEY for AI features)")
    
    def _check_admin_privileges(self) -> bool:
        """Check if running with admin privileges."""
        try:
            if platform.system() == 'Windows':
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin()
            else:
                return os.geteuid() == 0
        except:
            return False
    
    def scan_drives(self) -> List[Dict[str, Any]]:
        """Scan for available drives."""
        print("[SCAN] Scanning for available drives...")
        drives = []
        
        try:
            if self.system_info['os'] == 'Windows':
                drives = self._scan_windows_drives()
            elif self.system_info['os'] == 'Linux':
                drives = self._scan_linux_drives()
            elif self.system_info['os'] == 'Darwin':
                drives = self._scan_mac_drives()
            else:
                print(f"[ERROR] Unsupported OS: {self.system_info['os']}")
                return []
        
        except Exception as e:
            print(f"[ERROR] Error scanning drives: {e}")
            return []
        
        return drives
    
    def _scan_windows_drives(self) -> List[Dict[str, Any]]:
        """Scan drives on Windows using wmic."""
        try:
            result = subprocess.run([
                'wmic', 'diskdrive', 'get',
                'DeviceID,Model,Size,MediaType',
                '/format:csv'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise Exception(f"wmic command failed: {result.stderr}")
            
            drives = []
            lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            
            if len(lines) > 1:  # Skip header
                for line in lines[1:]:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 4 and parts[1]:  # Skip empty lines
                        try:
                            size_bytes = int(parts[3]) if parts[3] and parts[3].isdigit() else 0
                            size_gb = round(size_bytes / (1024**3), 2) if size_bytes else 0
                        except (ValueError, IndexError):
                            size_bytes = 0
                            size_gb = 0
                        
                        drives.append({
                            'device': parts[1],  # DeviceID
                            'model': parts[2] or 'Unknown',
                            'size': f"{size_gb} GB" if size_gb > 0 else "Unknown",
                            'size_bytes': size_bytes,
                            'media_type': parts[4] if len(parts) > 4 else 'Unknown'
                        })
            
            return drives
            
        except Exception as e:
            print(f"[ERROR] Windows drive scan failed: {e}")
            # Try alternative method with diskpart
            return self._scan_windows_diskpart_fallback()
    
    def _scan_windows_diskpart_fallback(self) -> List[Dict[str, Any]]:
        """Fallback method using diskpart to scan drives."""
        try:
            # Create temporary diskpart script
            script_content = "list disk\nexit\n"
            with open("diskpart_temp.txt", "w") as f:
                f.write(script_content)
            
            result = subprocess.run([
                'diskpart', '/s', 'diskpart_temp.txt'
            ], capture_output=True, text=True, timeout=30)
            
            # Clean up temp file
            try:
                os.remove("diskpart_temp.txt")
            except:
                pass
            
            if result.returncode != 0:
                print(f"[WARN] Diskpart fallback also failed: {result.stderr}")
                return []
            
            drives = []
            lines = result.stdout.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('Disk ') and not line.startswith('Disk ###'):
                    # Parse diskpart output: "Disk 0    Online      931 GB  1024 KB"
                    parts = line.split()
                    if len(parts) >= 4:
                        disk_num = parts[1]
                        status = parts[2] if len(parts) > 2 else 'Unknown'
                        size = f"{parts[3]} {parts[4]}" if len(parts) > 4 else 'Unknown'
                        
                        drives.append({
                            'device': f'\\\\.\\PhysicalDrive{disk_num}',
                            'model': f'Disk {disk_num}',
                            'size': size,
                            'status': status
                        })
            
            return drives
            
        except Exception as e:
            print(f"[WARN] Diskpart fallback failed: {e}")
            return []
    
    def _scan_linux_drives(self) -> List[Dict[str, Any]]:
        """Scan drives on Linux using lsblk."""
        try:
            result = subprocess.run([
                'lsblk', '-d', '-o', 'NAME,MODEL,SIZE,TYPE'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise Exception(f"lsblk command failed: {result.stderr}")
            
            drives = []
            lines = result.stdout.strip().split('\n')
            
            if len(lines) > 1:  # Skip header
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 4:
                        drives.append({
                            'device': f"/dev/{parts[0]}",
                            'model': parts[1] if len(parts[1]) > 1 else 'Unknown',
                            'size': parts[2],
                            'type': parts[3]
                        })
            
            return drives
            
        except Exception as e:
            print(f"[ERROR] Linux drive scan failed: {e}")
            return []
    
    def _scan_mac_drives(self) -> List[Dict[str, Any]]:
        """Scan drives on macOS using diskutil."""
        try:
            result = subprocess.run([
                'diskutil', 'list', '-plist'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise Exception(f"diskutil command failed: {result.stderr}")
            
            # This is a simplified version - real plist parsing would be better
            drives = []
            lines = result.stdout.split('\n')
            current_disk = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('/dev/disk'):
                    current_disk = line
                elif 'physical' in line.lower() and current_disk:
                    drives.append({
                        'device': current_disk,
                        'model': 'Unknown',
                        'size': 'Unknown',
                        'type': 'Physical'
                    })
            
            return drives
            
        except Exception as e:
            print(f"[ERROR] macOS drive scan failed: {e}")
            return []
    
    def display_drives(self, drives: List[Dict[str, Any]]):
        """Display found drives in a nice format."""
        if not drives:
            print("[ERROR] No drives found!")
            return
        
        print(f"\n[DRIVES] Found {len(drives)} drives:")
        print("=" * 60)
        
        for i, drive in enumerate(drives, 1):
            print(f"{i}. {drive['device']}")
            print(f"   Model: {drive.get('model', 'Unknown')}")
            print(f"   Size:  {drive.get('size', 'Unknown')}")
            if 'media_type' in drive:
                print(f"   Type:  {drive['media_type']}")
            print()
    
    def analyze_drive(self, drive_path: str) -> Dict[str, Any]:
        """Analyze a drive for corruption and recovery potential."""
        print(f"[ANALYZE] Analyzing drive: {drive_path}")
        
        analysis = {
            'drive_path': drive_path,
            'timestamp': datetime.now().isoformat(),
            'basic_check': self._basic_drive_check(drive_path),
            'ai_analysis': None
        }
        
        # Try AI analysis if available
        if self.drive_analyzer:
            try:
                print("[AI] Running AI analysis...")
                # Prepare the analysis data in the format expected by the LLM
                # The method expects partition -> status mappings
                partition_analysis = {}
                if analysis['basic_check']['accessible']:
                    partition_analysis['main_partition'] = 'accessible'
                else:
                    partition_analysis['main_partition'] = 'inaccessible'
                
                if analysis['basic_check']['readable']:
                    partition_analysis['boot_sector'] = 'readable'
                else:
                    partition_analysis['boot_sector'] = 'corrupted'
                
                if analysis['basic_check']['errors']:
                    partition_analysis['error_status'] = ', '.join(analysis['basic_check']['errors'])
                
                # Call the LLM method with correct parameters
                ai_summary, severity, recommendations = self.drive_analyzer.analyze_drive_corruption(
                    partition_analysis, 
                    {'name': 'SD Card', 'size': 'Unknown', 'type': 'Removable'}
                )
                
                analysis['ai_analysis'] = {
                    'summary': ai_summary,
                    'severity': severity,
                    'recommendations': recommendations,
                    'corruption_detected': 'corrupted' in ai_summary.lower() or severity != 'low'
                }
            except Exception as e:
                print(f"[WARN] AI analysis failed: {e}")
                analysis['ai_analysis'] = {'error': str(e)}
        
        return analysis
    
    def _basic_drive_check(self, drive_path: str) -> Dict[str, Any]:
        """Basic drive health check without AI."""
        check_result = {
            'accessible': False,
            'readable': False,
            'file_systems': [],
            'errors': []
        }
        
        try:
            # Check if drive exists and is accessible
            if self.system_info['os'] == 'Windows':
                # Windows drive check
                if os.path.exists(drive_path):
                    check_result['accessible'] = True
                    try:
                        # Try to read first few bytes
                        with open(drive_path, 'rb') as f:
                            data = f.read(512)  # Read first sector
                            if data:
                                check_result['readable'] = True
                                check_result['first_sector_size'] = len(data)
                    except PermissionError:
                        check_result['errors'].append('Permission denied - try running as Administrator')
                    except Exception as e:
                        check_result['errors'].append(f'Read error: {e}')
            else:
                # Unix-like systems
                if os.path.exists(drive_path):
                    check_result['accessible'] = True
                    # Try basic file command to identify filesystem
                    try:
                        result = subprocess.run(['file', '-s', drive_path], 
                                               capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            check_result['file_info'] = result.stdout.strip()
                    except:
                        pass
        
        except Exception as e:
            check_result['errors'].append(f'Basic check failed: {e}')
        
        return check_result
    
    def create_recovery_clone(self, source_drive: str, output_dir: str, 
                             clone_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a recovery clone of the drive."""
        print(f"[CLONE] Creating recovery clone...")
        print(f"   Source: {source_drive}")
        print(f"   Output: {output_dir}")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate clone filename if not provided
        if not clone_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            drive_name = os.path.basename(source_drive).replace('/', '_').replace('\\', '_')
            clone_name = f"recovery_clone_{drive_name}_{timestamp}.img"
        
        clone_path = os.path.join(output_dir, clone_name)
        
        # Attempt cloning
        clone_result = {
            'success': False,
            'clone_path': clone_path,
            'method_used': None,
            'error': None,
            'recovery_suggestions': None
        }
        
        try:
            if self.system_info['os'] == 'Windows':
                clone_result = self._windows_clone(source_drive, clone_path)
            else:
                clone_result = self._unix_clone(source_drive, clone_path)
        
        except Exception as e:
            clone_result['error'] = str(e)
        
        # If cloning failed and we have AI error handler, get suggestions
        if not clone_result['success'] and self.error_handler:
            try:
                print("[AI] Analyzing cloning failure...")
                recovery_analysis = self.error_handler.handle_drive_clone_error({
                    'error': clone_result['error'],
                    'source_path': source_drive,
                    'clone_dir': output_dir
                })
                clone_result['recovery_suggestions'] = recovery_analysis
            except Exception as e:
                print(f"[WARN] AI error analysis failed: {e}")
        
        return clone_result
    
    def _windows_clone(self, source_drive: str, clone_path: str) -> Dict[str, Any]:
        """Clone drive on Windows using multiple methods."""
        methods = [
            ('raw_copy', self._windows_raw_copy),
            ('powershell_stream', self._windows_powershell_clone),
            ('dd_for_windows', self._windows_dd_clone),
            ('filesystem_copy', self._windows_filesystem_copy)
        ]
        
        print(f"   [DEBUG] Admin privileges: {'YES' if self._check_admin_privileges() else 'NO'}")
        print(f"   [DEBUG] Source drive exists: {os.path.exists(source_drive)}")
        
        for method_name, method_func in methods:
            try:
                print(f"   [METHOD] Trying {method_name}...")
                result = method_func(source_drive, clone_path)
                if result['success']:
                    result['method_used'] = method_name
                    return result
                else:
                    print(f"   [FAILED] {method_name}: {result['error']}")
            except Exception as e:
                print(f"   [ERROR] {method_name} failed: {e}")
                continue
        
        return {
            'success': False,
            'error': 'All Windows cloning methods failed - try third-party tools like Win32DiskImager',
            'method_used': None
        }
    
    def _windows_raw_copy(self, source_drive: str, clone_path: str) -> Dict[str, Any]:
        """Try raw disk copy using Python's low-level file operations."""
        print(f"   [DEBUG] Attempting raw disk copy...")
        print(f"   [DEBUG] Source: {source_drive}")
        print(f"   [DEBUG] Target: {clone_path}")
        
        try:
            # First, try to get disk size using diskpart
            disk_size = None
            if 'PhysicalDrive' in source_drive:
                disk_num = source_drive.split('PhysicalDrive')[1]
                try:
                    # Use diskpart to get disk size
                    script_content = f"select disk {disk_num}\ndetail disk\nexit\n"
                    with open("diskpart_size_temp.txt", "w") as f:
                        f.write(script_content)
                    
                    result = subprocess.run([
                        'diskpart', '/s', 'diskpart_size_temp.txt'
                    ], capture_output=True, text=True, timeout=30)
                    
                    # Clean up temp file
                    try:
                        os.remove("diskpart_size_temp.txt")
                    except:
                        pass
                    
                    # Parse output for size
                    for line in result.stdout.split('\n'):
                        if 'Disk ID:' in line or 'Type   :' in line:
                            continue
                        if 'Status' in line and 'Size' in line:
                            # Look for size information
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if 'GB' in part or 'MB' in part:
                                    try:
                                        size_str = parts[i-1] + ' ' + part
                                        print(f"   [DEBUG] Found disk size: {size_str}")
                                    except:
                                        pass
                except Exception as e:
                    print(f"   [DEBUG] Could not determine disk size: {e}")
            
            # Attempt to open source drive with different access modes
            access_modes = [
                ('rb', 'Read-only binary mode'),
                ('r+b', 'Read-write binary mode')
            ]
            
            for mode, description in access_modes:
                try:
                    print(f"   [DEBUG] Trying to open source with {description}...")
                    
                    # Try to open the source drive
                    source_file = open(source_drive, mode)
                    print(f"   [DEBUG] Successfully opened source drive")
                    
                    # Create target file
                    print(f"   [DEBUG] Creating target file...")
                    target_file = open(clone_path, 'wb')
                    
                    # Start copying
                    chunk_size = 4 * 1024 * 1024  # 4MB chunks for better performance
                    total_copied = 0
                    last_progress_mb = 0
                    
                    print(f"   [DEBUG] Starting copy with {chunk_size} byte chunks...")
                    
                    while True:
                        try:
                            chunk = source_file.read(chunk_size)
                            if not chunk or len(chunk) == 0:
                                break
                            
                            target_file.write(chunk)
                            total_copied += len(chunk)
                            
                            # Progress reporting
                            current_mb = total_copied // (1024 * 1024)
                            if current_mb >= last_progress_mb + 50:  # Every 50MB
                                print(f"   [PROGRESS] Copied: {current_mb}MB ({total_copied} bytes)")
                                last_progress_mb = current_mb
                        
                        except Exception as read_error:
                            print(f"   [DEBUG] Read error at position {total_copied}: {read_error}")
                            # Try to skip bad sectors by seeking forward
                            try:
                                source_file.seek(total_copied + chunk_size)
                                # Write zeros for the bad sector
                                target_file.write(b'\x00' * chunk_size)
                                total_copied += chunk_size
                                print(f"   [DEBUG] Skipped bad sector, continuing...")
                            except:
                                print(f"   [DEBUG] Could not skip bad sector, ending copy")
                                break
                    
                    source_file.close()
                    target_file.close()
                    
                    print(f"   [DEBUG] Raw copy completed. Total: {total_copied} bytes")
                    
                    return {
                        'success': True,
                        'method_used': 'raw_copy',
                        'total_bytes': total_copied,
                        'message': f'Raw copy completed: {total_copied} bytes'
                    }
                
                except PermissionError as e:
                    print(f"   [DEBUG] Permission denied with {mode}: {e}")
                    continue
                except OSError as e:
                    print(f"   [DEBUG] OS error with {mode}: {e}")
                    continue
                except Exception as e:
                    print(f"   [DEBUG] Error with {mode}: {e}")
                    continue
            
            return {
                'success': False,
                'error': 'Could not access drive with any method - drive may be locked or require special drivers'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Raw copy failed: {e}'
            }
    
    def _windows_dd_clone(self, source_drive: str, clone_path: str) -> Dict[str, Any]:
        """Try dd for Windows if available."""
        # Check if dd.exe is available
        try:
            subprocess.run(['dd', '--version'], capture_output=True, timeout=5)
            dd_available = True
        except:
            dd_available = False
        
        if not dd_available:
            return {'success': False, 'error': 'dd not available on Windows'}
        
        # Run dd command
        cmd = [
            'dd',
            f'if={source_drive}',
            f'of={clone_path}',
            'bs=1M',
            'conv=noerror,sync'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'output': result.stdout,
                    'error': result.stderr if result.stderr else None
                }
            else:
                return {
                    'success': False,
                    'error': f"dd failed: {result.stderr}"
                }
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'dd operation timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"dd execution failed: {e}"
            }
    
    def _windows_powershell_clone(self, source_drive: str, clone_path: str) -> Dict[str, Any]:
        """Try PowerShell-based cloning using Win32_DiskDrive."""
        print(f"   [DEBUG] Attempting PowerShell disk imaging...")
        
        # Extract disk number from PhysicalDrive path
        disk_num = None
        if 'PhysicalDrive' in source_drive:
            try:
                disk_num = source_drive.split('PhysicalDrive')[1]
                print(f"   [DEBUG] Extracted disk number: {disk_num}")
            except:
                pass
        
        if not disk_num:
            return {
                'success': False,
                'error': 'Could not extract disk number from drive path'
            }
        
        # PowerShell script to copy disk using .NET streams
        ps_script = f'''
try {{
    $sourcePath = "{source_drive}"
    $destPath = "{clone_path}"
    
    Write-Host "[PS] Opening source disk: $sourcePath"
    $sourceStream = [System.IO.File]::OpenRead($sourcePath)
    
    Write-Host "[PS] Creating destination file: $destPath"
    $destStream = [System.IO.File]::Create($destPath)
    
    Write-Host "[PS] Starting copy operation..."
    $buffer = New-Object byte[] 1048576  # 1MB buffer
    $totalBytes = 0
    
    while ($true) {{
        $bytesRead = $sourceStream.Read($buffer, 0, $buffer.Length)
        if ($bytesRead -eq 0) {{ break }}
        
        $destStream.Write($buffer, 0, $bytesRead)
        $totalBytes += $bytesRead
        
        if ($totalBytes % 104857600 -eq 0) {{  # Every 100MB
            $mb = [math]::Round($totalBytes / 1048576, 1)
            Write-Host "[PS] Copied: ${{mb}}MB"
        }}
    }}
    
    $sourceStream.Close()
    $destStream.Close()
    
    Write-Host "[PS] Copy completed. Total: $totalBytes bytes"
    Write-Host "SUCCESS:$totalBytes"
    
}} catch {{
    Write-Host "ERROR:$($_.Exception.Message)"
    exit 1
}}
'''
        
        try:
            # Run PowerShell script
            result = subprocess.run([
                'powershell', '-ExecutionPolicy', 'Bypass', '-Command', ps_script
            ], capture_output=True, text=True, timeout=3600)
            
            print(f"   [DEBUG] PowerShell return code: {result.returncode}")
            print(f"   [DEBUG] PowerShell stdout: {result.stdout[:200]}...")
            
            if result.returncode == 0 and 'SUCCESS:' in result.stdout:
                # Extract total bytes from output
                for line in result.stdout.split('\n'):
                    if line.startswith('SUCCESS:'):
                        total_bytes = int(line.split(':')[1])
                        return {
                            'success': True,
                            'method_used': 'powershell_stream',
                            'total_bytes': total_bytes,
                            'output': result.stdout
                        }
            
            # Handle specific error cases
            if 'ERROR:' in result.stdout:
                error_msg = None
                for line in result.stdout.split('\n'):
                    if line.startswith('ERROR:'):
                        error_msg = line.split(':', 1)[1].strip()
                        break
                
                return {
                    'success': False,
                    'error': f'PowerShell cloning failed: {error_msg}'
                }
            else:
                return {
                    'success': False,
                    'error': f'PowerShell cloning failed: {result.stderr}'
                }
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'PowerShell cloning timed out (1 hour limit)'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'PowerShell cloning execution failed: {e}'
            }
    
    def _windows_filesystem_copy(self, source_drive: str, clone_path: str) -> Dict[str, Any]:
        """Try filesystem-level copy as last resort."""
        print(f"   [DEBUG] Attempting to open {source_drive} for reading...")
        
        try:
            # Check if we can access the drive directly
            with open(source_drive, 'rb') as source:
                print(f"   [DEBUG] Successfully opened source drive")
                print(f"   [DEBUG] Creating clone file: {clone_path}")
                
                # Read in chunks to avoid memory issues
                chunk_size = 1024 * 1024  # 1MB chunks
                total_size = 0
                
                with open(clone_path, 'wb') as target:
                    print(f"   [DEBUG] Starting copy operation...")
                    while True:
                        chunk = source.read(chunk_size)
                        if not chunk:
                            break
                        target.write(chunk)
                        total_size += len(chunk)
                        
                        # Progress indicator every 100MB
                        if total_size % (100 * 1024 * 1024) == 0:
                            print(f"   [PROGRESS] Copied: {total_size // (1024*1024)}MB")
                
                print(f"   [DEBUG] Copy completed. Total size: {total_size} bytes")
                return {
                    'success': True,
                    'method_used': 'filesystem_copy',
                    'total_bytes': total_size,
                    'message': f'Successfully copied {total_size} bytes'
                }
                
        except PermissionError as e:
            print(f"   [DEBUG] Permission error: {e}")
            return {
                'success': False,
                'error': f'Permission denied - requires Administrator privileges. Details: {e}'
            }
        except FileNotFoundError as e:
            print(f"   [DEBUG] File not found: {e}")
            return {
                'success': False,
                'error': f'Drive not found: {source_drive}. Details: {e}'
            }
        except OSError as e:
            print(f"   [DEBUG] OS error: {e}")
            # Check if it's a sharing violation (drive in use)
            if "sharing violation" in str(e).lower() or "being used by another process" in str(e).lower():
                return {
                    'success': False,
                    'error': f'Drive is in use by another process. Try: 1) Safely eject the drive and reinsert, 2) Close any file explorers showing the drive, 3) Restart and try again. Details: {e}'
                }
            else:
                return {
                    'success': False,
                    'error': f'OS error accessing drive: {e}'
                }
        except Exception as e:
            print(f"   [DEBUG] Unexpected error: {e}")
            return {
                'success': False,
                'error': f'Filesystem copy failed: {e}'
            }
    
    def _unix_clone(self, source_drive: str, clone_path: str) -> Dict[str, Any]:
        """Clone drive on Unix-like systems using dd."""
        cmd = [
            'dd',
            f'if={source_drive}',
            f'of={clone_path}',
            'bs=1M',
            'conv=noerror,sync',
            'status=progress'
        ]
        
        try:
            print(f"   Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'method_used': 'dd',
                    'output': result.stdout,
                    'error': result.stderr if result.stderr else None
                }
            else:
                return {
                    'success': False,
                    'error': f"dd failed: {result.stderr}"
                }
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'dd operation timed out (1 hour limit)'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"dd execution failed: {e}"
            }
    
    def display_analysis(self, analysis: Dict[str, Any]):
        """Display drive analysis results."""
        print("\n" + "="*60)
        print("[ANALYSIS] DRIVE ANALYSIS RESULTS")
        print("="*60)
        
        print(f"Drive: {analysis['drive_path']}")
        print(f"Time: {analysis['timestamp']}")
        
        # Basic check results
        basic = analysis['basic_check']
        print(f"\n[CHECK] Basic Check:")
        print(f"   Accessible: {'YES' if basic['accessible'] else 'NO'}")
        print(f"   Readable:   {'YES' if basic['readable'] else 'NO'}")
        
        if basic['errors']:
            print(f"   Errors:")
            for error in basic['errors']:
                print(f"     - {error}")
        
        # AI analysis results
        if analysis['ai_analysis'] and not analysis['ai_analysis'].get('error'):
            ai = analysis['ai_analysis']
            print(f"\n[AI] AI Analysis:")
            print(f"   Status: {ai.get('status', 'Unknown')}")
            if 'corruption_detected' in ai:
                print(f"   Corruption: {'DETECTED' if ai['corruption_detected'] else 'None detected'}")
            if 'recovery_plan' in ai:
                print(f"   Recovery Plan: {len(ai['recovery_plan'].get('steps', []))} steps")
        elif analysis['ai_analysis'] and analysis['ai_analysis'].get('error'):
            print(f"\n[WARN] AI Analysis Error: {analysis['ai_analysis']['error']}")
    
    def display_clone_result(self, result: Dict[str, Any]):
        """Display cloning results."""
        print("\n" + "="*60)
        print("[CLONE] CLONING RESULTS")
        print("="*60)
        
        if result['success']:
            print("[SUCCESS] Cloning completed successfully!")
            print(f"   Method: {result['method_used']}")
            print(f"   Clone saved to: {result['clone_path']}")
        else:
            print("[FAILED] Cloning failed!")
            print(f"   Error: {result['error']}")
            
            # Show AI recovery suggestions if available
            if result.get('recovery_suggestions'):
                suggestions = result['recovery_suggestions']
                if 'analysis' in suggestions:
                    analysis = suggestions['analysis']
                    print(f"\n[AI] AI Error Analysis:")
                    print(f"   Root Cause: {analysis.get('root_cause', 'Unknown')}")
                    
                    if 'solutions' in analysis and analysis['solutions']:
                        print(f"\n[SOLUTIONS] Suggested Solutions:")
                        for i, solution in enumerate(analysis['solutions'][:3], 1):
                            print(f"\n   {i}. {solution['name']} ({solution['probability']} probability)")
                            print(f"      Requirements: {', '.join(solution.get('requirements', []))}")
                            if solution.get('steps'):
                                print(f"      Steps:")
                                for step in solution['steps'][:3]:  # Show first 3 steps
                                    print(f"        - {step}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Standalone CLI Drive Recovery Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli_recovery.py --scan-drives
  python cli_recovery.py --recover --source /dev/disk2 --output ./recovery
  python cli_recovery.py --analyze-only --source /dev/disk2
        """
    )
    
    parser.add_argument('--scan-drives', action='store_true',
                       help='Scan and display available drives')
    
    parser.add_argument('--analyze-only', action='store_true',
                       help='Only analyze drive without cloning')
    
    parser.add_argument('--recover', action='store_true',
                       help='Full recovery: analyze + clone + fix')
    
    parser.add_argument('--source', type=str,
                       help='Source drive path (e.g., /dev/disk2 or \\\\.\\PhysicalDrive7)')
    
    parser.add_argument('--output', type=str, default='./recovery_output',
                       help='Output directory for clones and analysis (default: ./recovery_output)')
    
    parser.add_argument('--clone-name', type=str,
                       help='Custom name for clone file')
    
    args = parser.parse_args()
    
    # Create recovery tool instance
    recovery = CLIDriveRecovery()
    
    print("[TOOL] Standalone Drive Recovery Tool")
    print("=====================================")
    print(f"OS: {recovery.system_info['os']}")
    print(f"Admin privileges: {'YES' if recovery.system_info['is_admin'] else 'NO'}")
    
    if not recovery.system_info['is_admin']:
        print("[WARN] Note: Some operations require administrator privileges")
    
    # Handle scan drives
    if args.scan_drives:
        drives = recovery.scan_drives()
        recovery.display_drives(drives)
        return
    
    # Require source drive for other operations
    if not args.source:
        print("[ERROR] Error: --source is required for analysis and recovery operations")
        parser.print_help()
        return
    
    # Handle analyze only
    if args.analyze_only:
        analysis = recovery.analyze_drive(args.source)
        recovery.display_analysis(analysis)
        return
    
    # Handle full recovery
    if args.recover:
        print(f"\n[RECOVERY] Starting full recovery process...")
        
        # Step 1: Analyze
        print("\n[STEP 1] Drive Analysis")
        analysis = recovery.analyze_drive(args.source)
        recovery.display_analysis(analysis)
        
        # Step 2: Clone
        print(f"\n[STEP 2] Creating Recovery Clone")
        clone_result = recovery.create_recovery_clone(
            args.source, 
            args.output, 
            args.clone_name
        )
        recovery.display_clone_result(clone_result)
        
        # Step 3: Recovery recommendations
        print(f"\n[STEP 3] Recovery Recommendations")
        if clone_result['success']:
            print("[SUCCESS] Clone created successfully! Next steps:")
            print("   1. Verify clone integrity")
            print("   2. Work on clone, not original drive")
            print("   3. Use fsck or chkdsk to repair filesystem")
            print("   4. Extract recoverable data")
        else:
            print("[FAILED] Clone creation had issues. Consider:")
            print("   1. Running as Administrator (Windows)")
            print("   2. Using specialized recovery software")
            print("   3. Professional data recovery services")
            if clone_result.get('recovery_suggestions'):
                print("   4. See AI suggestions above")
        
        return
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()
