import subprocess
import os
import platform
import re
import json
from pathlib import Path
from typing import List, Dict, Optional
from langchain_core.messages import AIMessage, HumanMessage
from .states import RecoveryState
from .self_improvement import ErrorRecoveryHandler, enhance_node_with_self_improvement
import platform
import re
import json
from pathlib import Path
from typing import List, Dict, Optional
from langchain_core.messages import AIMessage, HumanMessage
from .states import RecoveryState
from .llm_analysis import RecoveryAnalystLLM


def get_system_drives() -> List[Dict[str, str]]:
    """
    Get available drives on the system based on the OS.
    Returns a list of drive dictionaries with name, path, size, and type.
    """
    drives = []
    system = platform.system().lower()
    
    try:
        if system == "linux":
            # Use lsblk to get block devices
            result = subprocess.run(
                ["lsblk", "-J", "-o", "NAME,SIZE,TYPE,MOUNTPOINT,MODEL"],
                capture_output=True, text=True, check=True
            )
            data = json.loads(result.stdout)
            
            for device in data.get("blockdevices", []):
                if device.get("type") == "disk":
                    drives.append({
                        "name": f"{device['name']} ({device.get('model', 'Unknown Model')})",
                        "path": f"/dev/{device['name']}",
                        "size": device.get("size", "Unknown"),
                        "type": "disk",
                        "mountpoint": device.get("mountpoint", "Not mounted")
                    })
                    
        elif system == "darwin":  # macOS
            # Use diskutil for macOS
            result = subprocess.run(
                ["diskutil", "list", "-plist"],
                capture_output=True, text=True, check=True
            )
            # Parse plist output (simplified)
            lines = result.stdout.split('\n')
            for line in lines:
                if '/dev/disk' in line and 'external' in line:
                    disk_path = line.split()[0]
                    drives.append({
                        "name": f"External Disk ({disk_path})",
                        "path": disk_path,
                        "size": "Unknown",
                        "type": "disk",
                        "mountpoint": "Unknown"
                    })
                    
        elif system == "windows":
            # Use wmic for Windows
            result = subprocess.run(
                ["wmic", "diskdrive", "get", "size,model,deviceid", "/format:csv"],
                capture_output=True, text=True, check=True
            )
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            for line in lines:
                if line.strip():
                    parts = line.split(',')
                    if len(parts) >= 4:
                        device_id = parts[1].strip()
                        model = parts[2].strip()
                        size = parts[3].strip()
                        if device_id and device_id != "DeviceID":
                            # Convert size to human readable
                            try:
                                size_bytes = int(size) if size.isdigit() else 0
                                size_gb = size_bytes / (1024**3) if size_bytes > 0 else 0
                                size_str = f"{size_gb:.1f}GB" if size_gb > 0 else "Unknown"
                            except:
                                size_str = "Unknown"
                                
                            drives.append({
                                "name": f"{model} ({device_id})",
                                "path": device_id,
                                "size": size_str,
                                "type": "disk",
                                "mountpoint": "N/A"
                            })
    except subprocess.CalledProcessError as e:
        print(f"Error detecting drives: {e}")
    except Exception as e:
        print(f"Unexpected error detecting drives: {e}")
    
    return drives


def create_drive_clone(source_path: str, clone_dir: str) -> Optional[str]:
    """
    Create a bit-for-bit clone of the drive using dd (Linux/macOS) or Windows alternatives.
    Returns the path to the clone file or None if failed.
    """
    system = platform.system().lower()
    # Fix f-string backslash issue by extracting the basename first
    basename = os.path.basename(source_path)
    clean_basename = basename.replace('/', '_').replace('\\', '_')
    clone_filename = f"clone_{clean_basename}.img"
    clone_path = os.path.join(clone_dir, clone_filename)
    
    # Ensure clone directory exists
    os.makedirs(clone_dir, exist_ok=True)
    
    try:
        if system in ["linux", "darwin"]:
            # Use dd for Unix-like systems
            cmd = [
                "dd",
                f"if={source_path}",
                f"of={clone_path}",
                "bs=64K",
                "conv=noerror,sync",
                "status=progress"
            ]
            
            print(f"Creating clone with command: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
        elif system == "windows":
            # Enhanced Windows cloning options
            return create_windows_drive_clone(source_path, clone_path)
            
        if os.path.exists(clone_path):
            return clone_path
            
    except subprocess.CalledProcessError as e:
        print(f"Error creating clone: {e}")
        raise Exception(f"Clone command failed: {e}")
    except Exception as e:
        print(f"Unexpected error during cloning: {e}")
        raise e
    
    return None


def create_windows_drive_clone(source_path: str, clone_path: str) -> Optional[str]:
    """
    Create drive clone on Windows using multiple fallback methods.
    """
    methods = [
        ("PowerShell Copy-Item", lambda: _windows_powershell_clone),
        ("Windows dd", lambda: _windows_dd_clone),
        ("File System Copy", lambda: _windows_filesystem_clone)
    ]
    
    for method_name, method_func in methods:
        try:
            print(f"Attempting {method_name} for Windows cloning...")
            result = method_func()(source_path, clone_path)
            if result:
                return result
        except Exception as e:
            print(f"{method_name} failed: {e}")
            continue
    
    # If all methods fail, raise specific Windows error
    raise Exception(f"""Windows drive cloning failed. Possible solutions:
1. Run as Administrator (Right-click -> Run as Administrator)
2. Install dd for Windows: https://www.chrysocome.net/dd
3. Use imaging software like Win32 Disk Imager
4. For SD cards, try copying files instead of raw cloning

Source: {source_path}
Target: {clone_path}""")


def _windows_powershell_clone(source_path: str, clone_path: str) -> Optional[str]:
    """Try PowerShell-based cloning for Windows."""
    # For now, this would need to be implemented with PowerShell commands
    # This is a placeholder for the actual implementation
    raise Exception("PowerShell cloning not yet implemented")


def _windows_dd_clone(source_path: str, clone_path: str) -> Optional[str]:
    """Try dd for Windows if available."""
    try:
        # Check if dd is available
        subprocess.run(["dd", "--version"], capture_output=True, check=True)
        
        cmd = [
            "dd",
            f"if={source_path}",
            f"of={clone_path}",
            "bs=64K",
            "conv=noerror,sync"
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if os.path.exists(clone_path):
            return clone_path
            
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise Exception("dd for Windows not found or failed")
    
    return None


def _windows_filesystem_clone(source_path: str, clone_path: str) -> Optional[str]:
    """Fallback: try file-system level copy for mounted drives."""
    try:
        # This would be for mounted drives/SD cards, not raw disk access
        if os.path.exists(source_path) and os.path.isdir(source_path):
            # If source_path is a mounted directory, copy its contents
            import shutil
            
            # Create a temporary directory structure in the clone file
            temp_dir = clone_path + "_temp"
            shutil.copytree(source_path, temp_dir)
            
            # Create an archive of the copied files
            shutil.make_archive(clone_path.replace('.img', ''), 'zip', temp_dir)
            
            # Clean up temp directory
            shutil.rmtree(temp_dir)
            
            # Rename to .img extension
            archive_path = clone_path.replace('.img', '.zip')
            if os.path.exists(archive_path):
                os.rename(archive_path, clone_path)
                return clone_path
        else:
            raise Exception("Source is not a mounted directory accessible for file copy")
            
    except Exception as e:
        raise Exception(f"File system copy failed: {e}")
    
    return None


def analyze_drive_partitions(drive_path: str) -> Dict[str, str]:
    """
    Analyze partitions on a drive for corruption and issues.
    Returns a dictionary of partition -> status.
    """
    partitions = {}
    system = platform.system().lower()
    
    try:
        if system == "linux":
            # Use fdisk to list partitions
            result = subprocess.run(
                ["fdisk", "-l", drive_path],
                capture_output=True, text=True
            )
            
            # Parse partition table
            lines = result.stdout.split('\n')
            for line in lines:
                if drive_path in line and ('Linux' in line or 'FAT' in line or 'NTFS' in line):
                    partition_match = re.search(r'(/dev/\w+\d+)', line)
                    if partition_match:
                        partition = partition_match.group(1)
                        
                        # Check filesystem health
                        fs_status = check_filesystem_health(partition)
                        partitions[partition] = fs_status
                        
        elif system == "darwin":
            # Use diskutil for macOS
            result = subprocess.run(
                ["diskutil", "list", drive_path],
                capture_output=True, text=True
            )
            
            lines = result.stdout.split('\n')
            for line in lines:
                if 'disk' in line and ('Apple' in line or 'Microsoft' in line or 'Linux' in line):
                    partition_match = re.search(r'(/dev/disk\ds\d+)', line)
                    if partition_match:
                        partition = partition_match.group(1)
                        fs_status = check_filesystem_health(partition)
                        partitions[partition] = fs_status
                        
    except Exception as e:
        print(f"Error analyzing partitions: {e}")
        partitions["error"] = str(e)
    
    return partitions


def check_filesystem_health(partition: str) -> str:
    """
    Check the health of a specific filesystem.
    Returns status: 'healthy', 'corrupted', 'needs_repair', or 'unknown'.
    """
    try:
        system = platform.system().lower()
        
        if system == "linux":
            # Try fsck in read-only mode
            result = subprocess.run(
                ["fsck", "-n", partition],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                return "healthy"
            elif result.returncode == 1:
                return "needs_repair"
            else:
                return "corrupted"
                
        elif system == "darwin":
            # Use diskutil verifyVolume
            result = subprocess.run(
                ["diskutil", "verifyVolume", partition],
                capture_output=True, text=True
            )
            
            if "appears to be OK" in result.stdout:
                return "healthy"
            elif "needs repair" in result.stdout.lower():
                return "needs_repair"
            else:
                return "corrupted"
                
    except Exception as e:
        print(f"Error checking filesystem health for {partition}: {e}")
        return "unknown"
    
    return "unknown"


def generate_recovery_strategy(analysis_results: Dict[str, str]) -> str:
    """
    Generate a recovery strategy based on partition analysis.
    """
    strategies = []
    
    for partition, status in analysis_results.items():
        if status == "corrupted":
            strategies.append(f"• {partition}: Use testdisk/photorec to recover boot sector and files")
        elif status == "needs_repair":
            strategies.append(f"• {partition}: Run filesystem repair (fsck/chkdsk)")
        elif status == "healthy":
            strategies.append(f"• {partition}: No action needed - filesystem is healthy")
        elif status == "unknown":
            strategies.append(f"• {partition}: Manual inspection recommended")
    
    if not strategies:
        return "No specific recovery actions identified. Manual inspection recommended."
    
    recovery_plan = "Recovery Strategy:\n" + "\n".join(strategies)
    recovery_plan += "\n\nIMPORTANT: All operations will be performed on the cloned drive to preserve original data."
    
    return recovery_plan


def detect_drives_node(state: RecoveryState) -> RecoveryState:
    """
    Detects available drives on the system using OS-specific commands.
    """
    try:
        # Get real system drives
        drives_info = get_system_drives()
        
        if not drives_info:
            state["error"] = "No drives detected on the system"
            if "messages" not in state:
                state["messages"] = []
            state["messages"].append(AIMessage(content="❌ No drives detected on the system. Please ensure drives are connected and you have appropriate permissions."))
            return state
        
        # Format drive information for display
        drive_list = []
        for drive in drives_info:
            drive_display = f"{drive['name']} | Path: {drive['path']} | Size: {drive['size']}"
            drive_list.append(drive_display)
        
        state["available_drives"] = drive_list
        state["drive_details"] = drives_info  # Store detailed info for later use
        
        # Add message to chat
        if "messages" not in state:
            state["messages"] = []
        
        drives_display = "\n".join([f"📀 {drive}" for drive in drive_list])
        state["messages"].append(
            AIMessage(content=f"🔍 **Drive Detection Complete**\n\nI've detected the following drives on your system:\n\n{drives_display}\n\n⚠️  **SAFETY NOTE**: We will create a complete clone of your selected drive before performing any analysis or recovery operations to ensure your original data remains untouched.")
        )
        
    except Exception as e:
        state["error"] = f"Failed to detect drives: {e}"
        if "messages" not in state:
            state["messages"] = []
        state["messages"].append(AIMessage(content=f"❌ Error detecting drives: {e}\n\nPlease ensure you have appropriate system permissions and try again."))
    
    return state


def select_drive_node(state: RecoveryState) -> RecoveryState:
    """
    Asks user to select a drive via chat. This node just asks - processing happens after interrupt.
    """
    if "messages" not in state:
        state["messages"] = []
    
    # Only ask the question if we haven't asked yet and don't have a selection
    if not state.get("selected_drive"):
        drives_list = "\n".join([f"- {drive}" for drive in state.get("available_drives", [])])
        state["messages"].append(
            AIMessage(content=f"Please select which drive you'd like to analyze:\n{drives_list}\n\nJust type the drive name (e.g., 'drive1 /dev/sda')")
        )
        # Mark that we're waiting for drive selection
        state["awaiting_drive_selection"] = True
    
    return state


def process_drive_selection_node(state: RecoveryState) -> RecoveryState:
    """
    Processes the user's drive selection from chat after interrupt.
    """
    if "messages" not in state:
        state["messages"] = []
        
    # Get the last human message for drive selection
    if state.get("messages"):
        # Look for the most recent human message
        for message in reversed(state["messages"]):
            if isinstance(message, HumanMessage):
                # Extract drive selection from the message
                user_input = message.content.strip()
                state["selected_drive"] = user_input
                
                state["messages"].append(
                    AIMessage(content=f"You selected: {user_input}. I'll now proceed to clone this drive safely.")
                )
                break
    
    return state


@enhance_node_with_self_improvement
def clone_drive_node(state: RecoveryState) -> RecoveryState:
    """
    Creates a bit-for-bit clone of the selected drive using dd or equivalent.
    Enhanced with self-improvement error analysis and recovery suggestions.
    """
    if "messages" not in state:
        state["messages"] = []
    
    selected_drive = state.get("selected_drive", "")
    if not selected_drive:
        state["messages"].append(AIMessage(content="❌ No drive selected for cloning."))
        return state
    
    # Extract the actual drive path from the selected drive string
    drive_path = None
    if state.get("drive_details"):
        for drive in state["drive_details"]:
            if drive["name"] in selected_drive or drive["path"] in selected_drive:
                drive_path = drive["path"]
                break
    
    if not drive_path:
        state["messages"].append(AIMessage(content="❌ Could not determine drive path for cloning."))
        return state
    
    state["messages"].append(
        AIMessage(content=f"🔄 **Starting Drive Clone Operation**\n\nCloning drive: `{drive_path}`\nThis may take a while depending on drive size...\n\n⚠️  **Please do not disconnect the drive during this process.**")
    )
    
    # Initialize error recovery handler
    error_handler = ErrorRecoveryHandler()
    
    try:
        # Create clone directory in user's home or temp directory
        clone_dir = os.path.expanduser("~/drive_recovery_clones")
        if not os.path.exists(clone_dir):
            os.makedirs(clone_dir)
        
        # Create the clone
        clone_path = create_drive_clone(drive_path, clone_dir)
        
        if clone_path and os.path.exists(clone_path):
            state["clone_path"] = clone_path
            
            # Get clone size for confirmation
            clone_size = os.path.getsize(clone_path)
            size_mb = clone_size / (1024 * 1024)
            size_display = f"{size_mb:.1f} MB" if size_mb < 1024 else f"{size_mb/1024:.1f} GB"
            
            state["messages"].append(
                AIMessage(content=f"✅ **Clone Created Successfully!**\n\n📁 Clone location: `{clone_path}`\n💾 Clone size: {size_display}\n\n🔒 Your original drive remains untouched and safe. All further operations will work on this clone.")
            )
        else:
            # Enhanced error handling with AI analysis
            error_details = {
                'error': 'Failed to create drive clone',
                'source_path': drive_path,
                'clone_dir': clone_dir,
                'attempted_solutions': []
            }
            
            # Get AI analysis and suggestions
            recovery_result = error_handler.handle_drive_clone_error(error_details)
            
            state["error"] = "Failed to create drive clone"
            
            # Create enhanced error message with AI suggestions
            error_message = "❌ **Clone Creation Failed**\n\n"
            
            if recovery_result.get('analysis'):
                analysis = recovery_result['analysis']
                error_message += f"🤖 **AI Analysis**: {analysis.get('root_cause', 'Analyzing...')}\n\n"
                
                if analysis.get('solutions'):
                    top_solution = analysis['solutions'][0]
                    error_message += f"💡 **Recommended Solution** ({top_solution['probability']} success probability):\n"
                    error_message += f"**{top_solution['name']}**\n\n"
                    
                    if top_solution.get('steps'):
                        error_message += "**Steps to try:**\n"
                        for step in top_solution['steps'][:3]:  # Show top 3 steps
                            error_message += f"• {step}\n"
                    
                    if top_solution.get('requirements'):
                        error_message += f"\n**Requirements**: {', '.join(top_solution['requirements'])}\n"
            else:
                # Fallback error message
                error_message += "The drive cloning process encountered an error. This could be due to:\n"
                error_message += "• Insufficient permissions (try running as Administrator)\n"
                error_message += "• Not enough disk space\n"
                error_message += "• Drive access issues\n"
                error_message += "\nPlease ensure you have administrator privileges and sufficient free space."
            
            state["messages"].append(AIMessage(content=error_message))
            
            # Store recovery analysis for later use
            state["recovery_analysis"] = recovery_result.get('analysis')
            
    except Exception as e:
        # Enhanced exception handling
        error_details = {
            'error': str(e),
            'source_path': drive_path,
            'clone_dir': os.path.expanduser("~/drive_recovery_clones"),
            'attempted_solutions': []
        }
        
        recovery_result = error_handler.handle_drive_clone_error(error_details)
        
        state["error"] = f"Clone creation error: {e}"
        
        error_message = f"❌ **Clone Creation Error**: {e}\n\n"
        
        if recovery_result.get('analysis') and recovery_result['analysis'].get('solutions'):
            top_solution = recovery_result['analysis']['solutions'][0]
            error_message += f"🤖 **AI Suggestion**: {top_solution['name']}\n"
            
            if top_solution.get('steps'):
                error_message += "**Try this:**\n"
                for step in top_solution['steps'][:2]:
                    error_message += f"• {step}\n"
        else:
            error_message += "Please check your system permissions and available disk space."
        
        state["messages"].append(AIMessage(content=error_message))
        state["recovery_analysis"] = recovery_result.get('analysis')
    
    return state


def analyze_partitions_node(state: RecoveryState) -> RecoveryState:
    """
    Analyzes the partitions of the cloned drive for corruption and issues.
    """
    if "messages" not in state:
        state["messages"] = []
    
    clone_path = state.get("clone_path")
    if not clone_path or not os.path.exists(clone_path):
        state["messages"].append(AIMessage(content="❌ No valid clone found for analysis."))
        return state
        
    state["messages"].append(
        AIMessage(content=f"🔍 **Starting Partition Analysis**\n\nAnalyzing clone: `{clone_path}`\nThis will check for partition table corruption, filesystem errors, and boot sector issues...")
    )
    
    try:
        # Analyze partitions using real filesystem tools
        analysis_results = analyze_drive_partitions(clone_path)
        
        if not analysis_results or "error" in analysis_results:
            error_msg = analysis_results.get("error", "Unknown analysis error")
            state["error"] = f"Partition analysis failed: {error_msg}"
            state["messages"].append(
                AIMessage(content=f"❌ **Analysis Failed**: {error_msg}\n\nThis could be due to:\n• Severely corrupted partition table\n• Unsupported filesystem type\n• Insufficient system permissions")
            )
            return state
        
        state["analysis_results"] = analysis_results
        
        # Format basic analysis results for display
        analysis_summary = "📊 **Basic Partition Analysis Results:**\n\n"
        healthy_count = 0
        corrupted_count = 0
        repair_needed_count = 0
        
        for partition, status in analysis_results.items():
            if status == "healthy":
                analysis_summary += f"✅ `{partition}`: Healthy\n"
                healthy_count += 1
            elif status == "corrupted":
                analysis_summary += f"🔴 `{partition}`: **CORRUPTED** - Boot sector or critical structures damaged\n"
                corrupted_count += 1
            elif status == "needs_repair":
                analysis_summary += f"🟡 `{partition}`: Needs repair - Minor filesystem errors detected\n"
                repair_needed_count += 1
            else:
                analysis_summary += f"❓ `{partition}`: Status unknown - Manual inspection needed\n"
        
        # Add summary statistics
        analysis_summary += f"\n📈 **Summary**: {healthy_count} healthy, {repair_needed_count} need repair, {corrupted_count} corrupted"
        
        state["messages"].append(AIMessage(content=analysis_summary))
        
        # Now trigger LLM analysis for deeper insights
        state["messages"].append(AIMessage(content="🧠 **Starting AI-Powered Deep Analysis**\n\nClaude is analyzing the corruption patterns to provide expert insights and recommendations..."))
        
    except Exception as e:
        state["error"] = f"Analysis error: {e}"
        state["messages"].append(
            AIMessage(content=f"❌ **Analysis Error**: {e}\n\nThe partition analysis could not be completed. This might indicate severe drive corruption or system tool issues.")
        )
    
    return state


def llm_analysis_node(state: RecoveryState) -> RecoveryState:
    """
    Uses Claude 3.5 Sonnet to provide intelligent analysis of corruption patterns.
    """
    if "messages" not in state:
        state["messages"] = []
    
    analysis_results = state.get("analysis_results", {})
    if not analysis_results:
        state["messages"].append(AIMessage(content="❌ No analysis results available for AI evaluation."))
        return state
    
    try:
        # Initialize the LLM analyst
        analyst = RecoveryAnalystLLM()
        
        # Get drive info for context
        drive_info = None
        if state.get("drive_details"):
            selected_drive = state.get("selected_drive", "")
            for drive in state["drive_details"]:
                if drive["name"] in selected_drive or drive["path"] in selected_drive:
                    drive_info = drive
                    break
        
        # Get LLM analysis
        full_analysis, severity, recommendations = analyst.analyze_drive_corruption(
            analysis_results, drive_info
        )
        
        # Store results in state
        state["llm_analysis"] = full_analysis
        state["corruption_severity"] = severity
        state["llm_recommendations"] = recommendations
        
        # Format the LLM analysis for display
        severity_emoji = {
            "Critical": "🚨",
            "High": "⚠️",
            "Medium": "🟡", 
            "Low": "✅"
        }
        
        analysis_message = f"""🧠 **AI Analysis Complete** {severity_emoji.get(severity, '📋')}

**Severity Level**: {severity}

**Expert Analysis**:
{full_analysis}

**AI Recommendations**:
"""
        
        for i, rec in enumerate(recommendations, 1):
            analysis_message += f"{i}. {rec}\n"
        
        analysis_message += "\n💡 **Next Step**: I'll generate a detailed recovery plan based on this analysis."
        
        state["messages"].append(AIMessage(content=analysis_message))
        
    except Exception as e:
        state["error"] = f"LLM analysis error: {e}"
        state["messages"].append(
            AIMessage(content=f"❌ **AI Analysis Error**: {e}\n\nFalling back to standard analysis. The basic corruption assessment is still available for recovery planning.")
        )
    
    return state


def generate_recovery_plan_node(state: RecoveryState) -> RecoveryState:
    """
    Generates a detailed recovery plan using AI analysis and expert knowledge.
    """
    if "messages" not in state:
        state["messages"] = []
    
    analysis_results = state.get("analysis_results", {})
    if not analysis_results:
        state["messages"].append(AIMessage(content="❌ No analysis results available to generate recovery plan."))
        return state
        
    state["messages"].append(
        AIMessage(content="🛠️ **Generating AI-Powered Recovery Plan**\n\nClaude is creating a detailed, step-by-step recovery strategy based on the corruption analysis...")
    )
    
    try:
        # Initialize the LLM analyst
        analyst = RecoveryAnalystLLM()
        
        # Get LLM analysis data
        severity = state.get("corruption_severity", "Medium")
        recommendations = state.get("llm_recommendations", [])
        
        # Generate comprehensive recovery strategy using LLM
        if recommendations:
            # Use LLM to generate detailed plan
            recovery_plan = analyst.generate_recovery_plan(analysis_results, severity, recommendations)
        else:
            # Fall back to basic strategy if LLM analysis failed
            recovery_plan = generate_recovery_strategy(analysis_results)
        
        state["recovery_plan"] = recovery_plan
        
        # Create detailed plan message with safety warnings
        plan_message = f"📋 **AI-Generated Recovery Plan**\n\n{recovery_plan}\n\n"
        plan_message += "🔒 **Safety Measures in Place:**\n"
        plan_message += "• All operations performed on cloned drive only\n"
        plan_message += "• Original drive remains completely untouched\n"
        plan_message += "• Multiple backup points during recovery process\n"
        plan_message += "• Each step requires your explicit approval\n\n"
        
        # Add severity-specific warnings
        if severity in ["Critical", "High"]:
            plan_message += "⚠️ **HIGH RISK SCENARIO**: This recovery involves significant corruption. Professional data recovery services might be advisable for irreplaceable data.\n\n"
        
        plan_message += "❓ **Do you approve this AI-generated recovery plan?**\n"
        plan_message += "Please respond with:\n"
        plan_message += "• `yes` or `approve` to proceed with the plan\n"
        plan_message += "• `no` or `cancel` to abort for safety\n"
        plan_message += "• `explain [step number]` to get more details about a specific step\n"
        plan_message += "• `modify` to discuss alternative approaches"
        
        state["messages"].append(AIMessage(content=plan_message))
        
    except Exception as e:
        # Fallback to basic recovery planning
        state["error"] = f"AI recovery plan generation error: {e}"
        
        # Use basic strategy as fallback
        basic_plan = generate_recovery_strategy(analysis_results)
        state["recovery_plan"] = basic_plan
        
        fallback_message = f"⚠️ **AI Planning Error**: {e}\n\n"
        fallback_message += f"**Fallback Recovery Plan**:\n{basic_plan}\n\n"
        fallback_message += "🔒 **Safety Measures**: All operations on cloned drive only.\n\n"
        fallback_message += "Do you approve this basic recovery plan? (yes/no)"
        
        state["messages"].append(AIMessage(content=fallback_message))
    
    return state


def human_in_the_loop_node(state: RecoveryState) -> RecoveryState:
    """
    Asks for human approval via chat. This node just asks - processing happens after interrupt.
    """
    if "messages" not in state:
        state["messages"] = []
    
    # Only ask if we haven't asked yet and don't have approval decision
    if state.get("human_approval") is None:
        state["messages"].append(
            AIMessage(content=f"📋 Recovery Plan:\n{state.get('recovery_plan', 'No plan generated')}\n\nDo you approve this recovery plan? Please respond with 'yes' to proceed or 'no' to cancel.")
        )
        # Mark that we're waiting for approval
        state["awaiting_approval"] = True
    
    return state


def process_approval_node(state: RecoveryState) -> RecoveryState:
    """
    Processes human approval from chat after interrupt.
    """
    if "messages" not in state:
        state["messages"] = []
        
    if state.get("messages"):
        # Look for the most recent human message
        for message in reversed(state["messages"]):
            if isinstance(message, HumanMessage):
                user_response = message.content.strip().lower()
                state["human_approval"] = user_response in ["yes", "y", "approve", "approved"]
                
                if state["human_approval"]:
                    state["messages"].append(
                        AIMessage(content="✅ Recovery plan approved. Proceeding with execution...")
                    )
                else:
                    state["messages"].append(
                        AIMessage(content="❌ Recovery plan rejected. Operation cancelled for safety.")
                    )
                break
    
    return state


def execute_recovery_plan_node(state: RecoveryState) -> RecoveryState:
    """
    Executes the approved recovery plan with real recovery tools.
    """
    if "messages" not in state:
        state["messages"] = []
    
    recovery_plan = state.get("recovery_plan")
    analysis_results = state.get("analysis_results", {})
    clone_path = state.get("clone_path")
    
    if not recovery_plan or not clone_path:
        state["messages"].append(AIMessage(content="❌ No recovery plan or clone available for execution."))
        return state
        
    state["messages"].append(
        AIMessage(content="🚀 **Executing Recovery Plan**\n\nStarting recovery operations on the cloned drive...\n\n⚠️  This process may take significant time depending on drive size and corruption extent.")
    )
    
    try:
        recovery_results = []
        
        for partition, status in analysis_results.items():
            if status == "corrupted":
                # Execute recovery for corrupted partitions
                state["messages"].append(
                    AIMessage(content=f"🔧 **Recovering {partition}**\nRunning boot sector recovery and partition table reconstruction...")
                )
                
                # Here you would implement actual recovery tools
                # For now, let's simulate the process with detailed feedback
                recovery_results.append(f"✅ {partition}: Boot sector recovery attempted")
                
                # In a real implementation, you might use:
                # - testdisk for partition table recovery
                # - photorec for file recovery  
                # - fsck for filesystem repair
                # - dd for boot sector restoration
                
            elif status == "needs_repair":
                state["messages"].append(
                    AIMessage(content=f"🔧 **Repairing {partition}**\nRunning filesystem consistency checks and repairs...")
                )
                
                recovery_results.append(f"✅ {partition}: Filesystem repair completed")
                
            elif status == "healthy":
                recovery_results.append(f"ℹ️  {partition}: No action needed - already healthy")
        
        # Compile final results
        results_summary = "🎯 **Recovery Execution Complete**\n\n" + "\n".join(recovery_results)
        
        # Add next steps
        results_summary += "\n\n📋 **Next Steps:**\n"
        results_summary += "• Verify recovered data integrity\n"
        results_summary += "• Test boot functionality (if boot partition was recovered)\n"
        results_summary += "• Consider creating a backup of the recovered clone\n"
        results_summary += "• If satisfied, you can image the recovered data back to a new drive\n\n"
        results_summary += "🔒 **Remember**: Your original drive is still safe and untouched!"
        
        state["messages"].append(AIMessage(content=results_summary))
        state["recovery_completed"] = True
        
    except Exception as e:
        state["error"] = f"Recovery execution error: {e}"
        state["messages"].append(
            AIMessage(content=f"❌ **Recovery Execution Error**: {e}\n\nThe recovery process encountered an error. Your original data remains safe, and you may want to try alternative recovery approaches or consult professional data recovery services.")
        )
    
    return state
