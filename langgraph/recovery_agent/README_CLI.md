# CLI Drive Recovery Tool

A standalone command-line drive recovery tool that works without LangGraph, LangSmith, or Studio dependencies.

## 🚀 Quick Start

### Basic Mode (No AI - Works Immediately)
```bash
# Scan available drives
python cli_recovery.py --scan-drives

# Analyze a drive (basic check only)
python cli_recovery.py --analyze-only --source /dev/disk2

# Full recovery: analyze + clone
python cli_recovery.py --recover --source /dev/disk2 --output ./recovery
```

### AI-Powered Mode (Optional)
1. Install dependencies: `pip install langchain-anthropic langchain-core`
2. Set API key: `export ANTHROPIC_API_KEY=your_key`
3. Run with full AI analysis and error recovery

## 📋 Commands

### Scan Drives
```bash
python cli_recovery.py --scan-drives
```
Lists all available storage devices with basic information.

### Analyze Only
```bash
python cli_recovery.py --analyze-only --source <drive_path>
```
Analyzes drive health and corruption without creating clones.

**Examples:**
- Windows: `--source \\.\PhysicalDrive7`
- Linux: `--source /dev/sdb`
- macOS: `--source /dev/disk2`

### Full Recovery
```bash
python cli_recovery.py --recover --source <drive_path> --output <output_dir>
```
Complete recovery process: analyze → clone → provide recommendations.

**Options:**
- `--output`: Directory for recovery files (default: ./recovery_output)
- `--clone-name`: Custom name for clone file

## 🔧 Features

### Basic Mode Features (Always Available)
- ✅ Multi-platform drive scanning (Windows/Linux/macOS)
- ✅ Drive accessibility and basic health checks
- ✅ Multiple cloning methods with automatic fallback
- ✅ Cross-platform cloning (dd on Unix, multiple methods on Windows)
- ✅ Clear error messages and troubleshooting hints

### AI-Powered Features (Optional)
- 🤖 Intelligent drive corruption analysis using Claude 3.5 Sonnet
- 🤖 Automatic error diagnosis and solution suggestions
- 🤖 Learning from previous failures to improve recommendations
- 🤖 Context-aware recovery planning based on drive condition

## 🖥️ Platform Support

### Windows
- Drive detection via `wmic`
- Multiple cloning methods:
  1. dd for Windows (if available)
  2. PowerShell imaging commands
  3. Filesystem-level copying
- Administrator privilege detection and guidance

### Linux/Unix
- Drive detection via `lsblk`
- dd-based cloning with progress monitoring
- Filesystem analysis via `file` command
- Root privilege detection

### macOS
- Drive detection via `diskutil`
- dd-based cloning
- Disk management integration

## ⚠️ Important Notes

### Administrator/Root Privileges
Many drive operations require elevated privileges:
- **Windows**: Run Command Prompt as Administrator
- **Linux/macOS**: Run with `sudo`

The tool will detect privilege levels and provide guidance.

### Safety First
- Always work on clones, never the original drive
- Verify clone integrity before making changes
- Keep multiple backup copies for critical data

### Error Recovery
If cloning fails, the tool provides:
1. Basic troubleshooting suggestions (always available)
2. AI-powered error analysis (if enabled)
3. Alternative cloning methods
4. Step-by-step recovery instructions

## 🔧 Troubleshooting

### "Permission Denied" Errors
1. Run as Administrator (Windows) or with sudo (Linux/macOS)
2. Ensure drive isn't mounted or in use
3. Check drive ownership and permissions

### "Module Not Found" Errors
- Basic mode works without any dependencies
- For AI features: `pip install langchain-anthropic langchain-core`
- Set `ANTHROPIC_API_KEY` environment variable

### Cloning Failures
1. Check available disk space (clones need space equal to source drive)
2. Verify source drive path is correct
3. Ensure target directory is writable
4. Try different cloning methods (tool attempts automatically)

## 🎯 Example Workflows

### Quick Health Check
```bash
# Scan drives
python cli_recovery.py --scan-drives

# Pick a drive and analyze
python cli_recovery.py --analyze-only --source /dev/sdb
```

### Full SD Card Recovery
```bash
# Create recovery directory
mkdir sd_card_recovery

# Full recovery process
python cli_recovery.py --recover \
    --source /dev/disk2 \
    --output ./sd_card_recovery \
    --clone-name "corrupted_sd_card.img"
```

### Windows Drive Recovery
```bash
# Run as Administrator
python cli_recovery.py --recover --source \\.\PhysicalDrive7 --output C:\Recovery
```

## 🔮 AI Features in Detail

When AI features are enabled (`ANTHROPIC_API_KEY` set):

### Intelligent Error Analysis
- Analyzes specific error messages and system context
- Provides root cause analysis
- Suggests ranked solutions by probability of success
- Learns from previous errors to improve suggestions

### Drive Corruption Detection
- Examines drive structure and filesystem patterns
- Identifies corruption types and recovery potential
- Generates step-by-step recovery plans
- Recommends appropriate tools and techniques

### Adaptive Recovery
- Adjusts strategies based on error patterns
- Suggests alternative approaches when primary methods fail
- Provides context-aware troubleshooting steps
- Maintains knowledge base of successful recovery patterns

## 📊 Output Examples

### Drive Scan Output
```
🔍 Scanning for available drives...
📱 Found 3 drives:
============================================================

1. \\.\PhysicalDrive0
   Model: Samsung SSD 980 PRO 1TB
   Size:  931.5 GB
   Type:  Fixed hard disk media

2. \\.\PhysicalDrive7
   Model: SanDisk Ultra 32GB USB
   Size:  29.8 GB
   Type:  Removable media

3. \\.\PhysicalDrive8
   Model: Generic SD Card
   Size:  7.4 GB
   Type:  Removable media
```

### Analysis Output
```
============================================================
📊 DRIVE ANALYSIS RESULTS
============================================================
Drive: \\.\PhysicalDrive8
Time: 2025-08-22T15:30:45.123456

🔍 Basic Check:
   Accessible: ✅
   Readable:   ❌
   Errors:
     • Permission denied - try running as Administrator

🤖 AI Analysis:
   Status: Corrupted boot sector detected
   Corruption: ⚠️  Detected
   Recovery Plan: 5 steps
```

This tool provides a complete standalone solution for drive recovery without requiring complex setup or web interfaces!
