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
    print("✅ Self-improvement module loaded")
except ImportError as e:
    print(f"⚠️  Self-improvement module unavailable: {e}")

try:
    from recovery_agent.llm_analysis import RecoveryAnalystLLM
    DriveAnalyzer = RecoveryAnalystLLM  # Use alias for compatibility
    print("✅ LLM analysis module loaded")
except ImportError as e:
    print(f"⚠️  LLM analysis module unavailable: {e}")
    DriveAnalyzer = None

if not (ErrorRecoveryHandler and DriveAnalyzer):
    print("ℹ️  Running in basic mode without AI features")
    print("   Install requirements and set ANTHROPIC_API_KEY for full functionality")


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
                print("🤖 AI error recovery enabled")
            else:
                print("ℹ️  AI error recovery unavailable")
        except Exception as e:
            print(f"⚠️  Could not initialize error recovery: {e}")
        
        try:
            if DriveAnalyzer and os.getenv('ANTHROPIC_API_KEY'):
                self.drive_analyzer = DriveAnalyzer()
                print("🤖 AI drive analysis enabled")
            else:
                print("ℹ️  AI drive analysis unavailable")
        except Exception as e:
            print(f"⚠️  Could not initialize drive analyzer: {e}")
        
        if not (self.error_handler or self.drive_analyzer):
            print("ℹ️  Running in basic mode (set ANTHROPIC_API_KEY for AI features)")
    
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
        print("🔍 Scanning for available drives...")
        drives = []
        
        try:
            if self.system_info['os'] == 'Windows':
                drives = self._scan_windows_drives()
            elif self.system_info['os'] == 'Linux':
                drives = self._scan_linux_drives()
            elif self.system_info['os'] == 'Darwin':
                drives = self._scan_mac_drives()
            else:
                print(f"❌ Unsupported OS: {self.system_info['os']}")
                return []
        
        except Exception as e:
            print(f"❌ Error scanning drives: {e}")
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
            print(f"❌ Windows drive scan failed: {e}")
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
                print(f"⚠️  Diskpart fallback also failed: {result.stderr}")
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
            print(f"⚠️  Diskpart fallback failed: {e}")
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
            print(f"❌ Linux drive scan failed: {e}")
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
            print(f"❌ macOS drive scan failed: {e}")
            return []
    
    def display_drives(self, drives: List[Dict[str, Any]]):
        """Display found drives in a nice format."""
        if not drives:
            print("❌ No drives found!")
            return
        
        print(f"\n📱 Found {len(drives)} drives:")
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
        print(f"🔍 Analyzing drive: {drive_path}")
        
        analysis = {
            'drive_path': drive_path,
            'timestamp': datetime.now().isoformat(),
            'basic_check': self._basic_drive_check(drive_path),
            'ai_analysis': None
        }
        
        # Try AI analysis if available
        if self.drive_analyzer:
            try:
                print("🤖 Running AI analysis...")
                ai_result = self.drive_analyzer.analyze_drive_corruption(drive_path)
                analysis['ai_analysis'] = ai_result
            except Exception as e:
                print(f"⚠️  AI analysis failed: {e}")
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
        print(f"💾 Creating recovery clone...")
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
                print("🤖 Analyzing cloning failure...")
                recovery_analysis = self.error_handler.handle_drive_clone_error({
                    'error': clone_result['error'],
                    'source_path': source_drive,
                    'clone_dir': output_dir
                })
                clone_result['recovery_suggestions'] = recovery_analysis
            except Exception as e:
                print(f"⚠️  AI error analysis failed: {e}")
        
        return clone_result
    
    def _windows_clone(self, source_drive: str, clone_path: str) -> Dict[str, Any]:
        """Clone drive on Windows using multiple methods."""
        methods = [
            ('dd_for_windows', self._windows_dd_clone),
            ('powershell_copy', self._windows_powershell_clone),
            ('filesystem_copy', self._windows_filesystem_clone)
        ]
        
        for method_name, method_func in methods:
            try:
                print(f"   Trying {method_name}...")
                result = method_func(source_drive, clone_path)
                if result['success']:
                    result['method_used'] = method_name
                    return result
            except Exception as e:
                print(f"   ❌ {method_name} failed: {e}")
                continue
        
        return {
            'success': False,
            'error': 'All Windows cloning methods failed',
            'method_used': None
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
        """Try PowerShell-based cloning."""
        # This is a placeholder for PowerShell imaging commands
        return {
            'success': False,
            'error': 'PowerShell cloning not yet implemented'
        }
    
    def _windows_filesystem_copy(self, source_drive: str, clone_path: str) -> Dict[str, Any]:
        """Try filesystem-level copy as last resort."""
        return {
            'success': False,
            'error': 'Filesystem copy not suitable for full drive cloning'
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
        print("📊 DRIVE ANALYSIS RESULTS")
        print("="*60)
        
        print(f"Drive: {analysis['drive_path']}")
        print(f"Time: {analysis['timestamp']}")
        
        # Basic check results
        basic = analysis['basic_check']
        print(f"\n🔍 Basic Check:")
        print(f"   Accessible: {'✅' if basic['accessible'] else '❌'}")
        print(f"   Readable:   {'✅' if basic['readable'] else '❌'}")
        
        if basic['errors']:
            print(f"   Errors:")
            for error in basic['errors']:
                print(f"     • {error}")
        
        # AI analysis results
        if analysis['ai_analysis'] and not analysis['ai_analysis'].get('error'):
            ai = analysis['ai_analysis']
            print(f"\n🤖 AI Analysis:")
            print(f"   Status: {ai.get('status', 'Unknown')}")
            if 'corruption_detected' in ai:
                print(f"   Corruption: {'⚠️  Detected' if ai['corruption_detected'] else '✅ None detected'}")
            if 'recovery_plan' in ai:
                print(f"   Recovery Plan: {len(ai['recovery_plan'].get('steps', []))} steps")
        elif analysis['ai_analysis'] and analysis['ai_analysis'].get('error'):
            print(f"\n⚠️  AI Analysis Error: {analysis['ai_analysis']['error']}")
    
    def display_clone_result(self, result: Dict[str, Any]):
        """Display cloning results."""
        print("\n" + "="*60)
        print("💾 CLONING RESULTS")
        print("="*60)
        
        if result['success']:
            print("✅ Cloning completed successfully!")
            print(f"   Method: {result['method_used']}")
            print(f"   Clone saved to: {result['clone_path']}")
        else:
            print("❌ Cloning failed!")
            print(f"   Error: {result['error']}")
            
            # Show AI recovery suggestions if available
            if result.get('recovery_suggestions'):
                suggestions = result['recovery_suggestions']
                if 'analysis' in suggestions:
                    analysis = suggestions['analysis']
                    print(f"\n🤖 AI Error Analysis:")
                    print(f"   Root Cause: {analysis.get('root_cause', 'Unknown')}")
                    
                    if 'solutions' in analysis and analysis['solutions']:
                        print(f"\n💡 Suggested Solutions:")
                        for i, solution in enumerate(analysis['solutions'][:3], 1):
                            print(f"\n   {i}. {solution['name']} ({solution['probability']} probability)")
                            print(f"      Requirements: {', '.join(solution.get('requirements', []))}")
                            if solution.get('steps'):
                                print(f"      Steps:")
                                for step in solution['steps'][:3]:  # Show first 3 steps
                                    print(f"        • {step}")


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
    
    print("🛠️  Standalone Drive Recovery Tool")
    print("=====================================")
    print(f"OS: {recovery.system_info['os']}")
    print(f"Admin privileges: {'✅' if recovery.system_info['is_admin'] else '❌'}")
    
    if not recovery.system_info['is_admin']:
        print("⚠️  Note: Some operations require administrator privileges")
    
    # Handle scan drives
    if args.scan_drives:
        drives = recovery.scan_drives()
        recovery.display_drives(drives)
        return
    
    # Require source drive for other operations
    if not args.source:
        print("❌ Error: --source is required for analysis and recovery operations")
        parser.print_help()
        return
    
    # Handle analyze only
    if args.analyze_only:
        analysis = recovery.analyze_drive(args.source)
        recovery.display_analysis(analysis)
        return
    
    # Handle full recovery
    if args.recover:
        print(f"\n🚀 Starting full recovery process...")
        
        # Step 1: Analyze
        print("\n📊 Step 1: Drive Analysis")
        analysis = recovery.analyze_drive(args.source)
        recovery.display_analysis(analysis)
        
        # Step 2: Clone
        print(f"\n💾 Step 2: Creating Recovery Clone")
        clone_result = recovery.create_recovery_clone(
            args.source, 
            args.output, 
            args.clone_name
        )
        recovery.display_clone_result(clone_result)
        
        # Step 3: Recovery recommendations
        print(f"\n📋 Step 3: Recovery Recommendations")
        if clone_result['success']:
            print("✅ Clone created successfully! Next steps:")
            print("   1. Verify clone integrity")
            print("   2. Work on clone, not original drive")
            print("   3. Use fsck or chkdsk to repair filesystem")
            print("   4. Extract recoverable data")
        else:
            print("❌ Clone creation failed. Consider:")
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
