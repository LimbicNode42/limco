#!/usr/bin/env python3
"""
Script to upgrade all MCP tools to use the hybrid connection strategy.

This script will:
1. Add MCPConnectionManager to each MCP tool file
2. Update tool functions to use hybrid connections (aggregator -> individual -> native)
3. Ensure consistent error handling and connection method reporting
4. Create integration tests for each tool
"""

import os
import re
import shutil
from pathlib import Path
from typing import List, Dict, Any

# MCP tool files to upgrade
MCP_TOOLS = [
    {
        "file": "mcp_file_operations.py",
        "servers": ["filescopemcp", "texteditor", "languageserver"],
        "config_name": "MCP_FILE_CONFIG",
        "manager_name": "MCPFileConnectionManager",
        "ports": {"filescopemcp": 6971, "texteditor": 6972, "languageserver": 6973}
    },
    {
        "file": "mcp_code_execution.py", 
        "servers": ["python-executor", "deno-executor"],
        "config_name": "MCP_EXEC_CONFIG",
        "manager_name": "MCPExecConnectionManager",
        "ports": {"python-executor": 6974, "deno-executor": 6975}
    },
    {
        "file": "mcp_code_analysis.py",
        "servers": ["serena", "repomapper"],
        "config_name": "MCP_ANALYSIS_CONFIG", 
        "manager_name": "MCPAnalysisConnectionManager",
        "ports": {"serena": 6976, "repomapper": 6977}
    },
    {
        "file": "github_mcp.py",
        "servers": ["github-mcp-server"],
        "config_name": "MCP_GITHUB_CONFIG",
        "manager_name": "MCPGitHubConnectionManager",
        "ports": {"github-mcp-server": 6978}
    }
]

def create_hybrid_header(tool_config: Dict[str, Any]) -> str:
    """Create the hybrid connection header for a tool file."""
    servers_config = ""
    for server, port in tool_config["ports"].items():
        env_var = f"{server.upper().replace('-', '_')}_MCP_PORT"
        servers_config += f'''        "{server}": {{
            "port": int(os.getenv("{env_var}", "{port}")),
            "host": "127.0.0.1",
            "start_command": ["{server}-mcp", "--transport", "sse"],
            "health_endpoint": "/health"
        }},
'''
    
    endpoints_config = ""
    for server in tool_config["servers"]:
        endpoints_config += f'        "{server}_endpoint": "/{server}",\n'
    
    return f'''
# MCP Server Configuration - Hybrid Approach
# Primary: Connect to MCP Aggregator/Proxy
# Secondary: Start individual MCP servers
{tool_config["config_name"]} = {{
    "aggregator": {{
        "enabled": True,
        "url": os.getenv("MCP_AGGREGATOR_URL", "http://localhost:8080"),
        "timeout": 5,
{endpoints_config}    }},
    "individual_servers": {{
{servers_config}    }},
    "fallback_native": True,
    "startup_timeout": 30,
    "health_check_interval": 10
}}
'''

def create_connection_manager_class(tool_config: Dict[str, Any]) -> str:
    """Create the connection manager class for a tool."""
    return f'''
class {tool_config["manager_name"]}:
    """Manages hybrid MCP connections - aggregator first, individual servers as fallback."""
    
    def __init__(self):
        self.config = {tool_config["config_name"]}
        self.aggregator_available = False
        self.individual_servers = {{}}
        self.server_processes = {{}}
        self._lock = threading.Lock()
        
    def check_aggregator_health(self) -> bool:
        """Check if MCP aggregator is available."""
        if not self.config["aggregator"]["enabled"]:
            return False
            
        try:
            url = self.config["aggregator"]["url"]
            timeout = self.config["aggregator"]["timeout"]
            response = requests.get(f"{{url}}/health", timeout=timeout)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Aggregator health check failed: {{e}}")
            return False
    
    def start_individual_server(self, server_name: str) -> bool:
        """Start an individual MCP server."""
        if server_name in self.server_processes:
            return True  # Already running
            
        config = self.config["individual_servers"].get(server_name)
        if not config:
            logger.error(f"No configuration found for server: {{server_name}}")
            return False
        
        # Check if command exists
        cmd_name = config["start_command"][0]
        if not self._check_command_exists(cmd_name):
            logger.warning(f"Command '{{cmd_name}}' not found, cannot start {{server_name}} server")
            return False
            
        try:
            # Build command with host and port
            cmd = config["start_command"] + [
                "--host", config["host"],
                "--port", str(config["port"])
            ]
            
            logger.info(f"Starting {{server_name}} MCP server: {{' '.join(cmd)}}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Store process reference
            with self._lock:
                self.server_processes[server_name] = process
            
            # Wait a bit for server to start
            time.sleep(2)
            
            # Check if server is healthy
            if self.check_individual_server_health(server_name):
                logger.info(f"{{server_name}} MCP server started successfully")
                return True
            else:
                logger.error(f"{{server_name}} MCP server failed health check")
                self.stop_individual_server(server_name)
                return False
                
        except Exception as e:
            logger.error(f"Failed to start {{server_name}} MCP server: {{e}}")
            return False
    
    def _check_command_exists(self, command: str) -> bool:
        """Check if a command exists in the system PATH."""
        try:
            subprocess.run([command, "--version"], capture_output=True, timeout=5)
            return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def check_individual_server_health(self, server_name: str) -> bool:
        """Check health of individual MCP server."""
        config = self.config["individual_servers"].get(server_name)
        if not config:
            return False
            
        try:
            url = f"http://{{config['host']}}:{{config['port']}}{{config['health_endpoint']}}"
            response = requests.get(url, timeout=2)
            return response.status_code == 200
        except Exception:
            return False
    
    def stop_individual_server(self, server_name: str):
        """Stop an individual MCP server."""
        with self._lock:
            if server_name in self.server_processes:
                process = self.server_processes[server_name]
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                except Exception as e:
                    logger.warning(f"Error stopping {{server_name}} server: {{e}}")
                finally:
                    del self.server_processes[server_name]
    
    def get_connection_info(self, server_type: str) -> Dict[str, Any]:
        """Get connection info for a server type."""
        # Try aggregator first
        if self.check_aggregator_health():
            aggregator_config = self.config["aggregator"]
            endpoint = aggregator_config.get(f"{{server_type}}_endpoint", f"/{{server_type}}")
            return {{
                "method": "aggregator",
                "url": f"{{aggregator_config['url']}}{{endpoint}}",
                "available": True
            }}
        
        # Try individual server
        with self._lock:
            if not self.check_individual_server_health(server_type):
                if self.start_individual_server(server_type):
                    config = self.config["individual_servers"][server_type]
                    return {{
                        "method": "individual",
                        "url": f"http://{{config['host']}}:{{config['port']}}",
                        "available": True
                    }}
            else:
                config = self.config["individual_servers"][server_type]
                return {{
                    "method": "individual",
                    "url": f"http://{{config['host']}}:{{config['port']}}",
                    "available": True
                }}
        
        # Fallback to native - always available
        return {{
            "method": "native",
            "url": None,
            "available": True  # Native implementations should always be available
        }}
    
    def cleanup(self):
        """Clean up all running servers."""
        for server_name in list(self.server_processes.keys()):
            self.stop_individual_server(server_name)


# Global connection manager instance
_mcp_{tool_config["file"].split("_")[1]}_manager = {tool_config["manager_name"]}()
'''

def create_hybrid_tool_wrapper(original_function: str, server_type: str, manager_var: str) -> str:
    """Create a hybrid tool wrapper for an existing function."""
    # Extract function signature and docstring
    lines = original_function.split('\n')
    
    # Find function definition
    func_start = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('def '):
            func_start = i
            break
    
    # Extract function name and arguments
    func_line = lines[func_start]
    func_name = func_line.split('(')[0].replace('def ', '').strip()
    
    # Build hybrid wrapper
    hybrid_wrapper = f'''
def {func_name}_hybrid(*args, **kwargs):
    """Hybrid wrapper for {func_name} using MCP connection strategy."""
    try:
        connection_info = {manager_var}.get_connection_info("{server_type}")
        
        if connection_info["method"] in ["aggregator", "individual"]:
            # Use MCP server
            payload = {{
                "method": "tools/call",
                "params": {{
                    "name": "{func_name}",
                    "arguments": kwargs if kwargs else dict(zip([...], args))  # Need to extract param names
                }}
            }}
            
            try:
                response = requests.post(
                    f"{{connection_info['url']}}/mcp",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    result["connection_method"] = connection_info["method"]
                    return result
                else:
                    logger.warning(f"MCP server returned {{response.status_code}}, falling back to native")
            except Exception as e:
                logger.warning(f"MCP connection failed: {{e}}, falling back to native")
        
        # Native fallback - call original function
        logger.info(f"Using native {{func_name}} implementation")
        result = {func_name}_native(*args, **kwargs)
        result["connection_method"] = "native"
        return result
        
    except Exception as e:
        logger.error(f"{{func_name}} failed: {{e}}")
        return {{
            "success": False,
            "error": f"{{func_name}} failed: {{str(e)}}",
            "connection_method": "native"
        }}
'''
    
    return hybrid_wrapper

def upgrade_mcp_tool_file(tool_config: Dict[str, Any], src_dir: Path):
    """Upgrade a single MCP tool file to use hybrid connections."""
    file_path = src_dir / tool_config["file"]
    
    print(f"\\n🔧 Upgrading {tool_config['file']}...")
    
    # Read original file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create backup
    backup_path = file_path.with_suffix('.py.backup')
    shutil.copy2(file_path, backup_path)
    print(f"   ✅ Created backup: {backup_path}")
    
    # Check if already upgraded
    if tool_config["manager_name"] in content:
        print(f"   ⚠️  Already upgraded, skipping...")
        return
    
    # Add required imports if not present
    imports_to_add = ["import time", "import threading", "import requests"]
    for imp in imports_to_add:
        if imp not in content:
            # Add after existing imports
            import_section = content.find("from langchain_core.tools import tool")
            if import_section != -1:
                content = content[:import_section] + imp + "\\n" + content[import_section:]
    
    # Add hybrid configuration after imports
    config_section = create_hybrid_header(tool_config)
    manager_section = create_connection_manager_class(tool_config)
    
    # Find insertion point (after imports, before first class/function)
    insertion_point = content.find("\\nclass ") 
    if insertion_point == -1:
        insertion_point = content.find("\\ndef ")
    if insertion_point == -1:
        insertion_point = content.find("\\n@tool")
    
    if insertion_point != -1:
        content = content[:insertion_point] + config_section + manager_section + content[insertion_point:]
    
    # Write updated content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"   ✅ Added hybrid connection infrastructure")

def create_integration_test(tool_config: Dict[str, Any], test_dir: Path):
    """Create integration test for upgraded MCP tool."""
    test_file = test_dir / f"test_{tool_config['file']}"
    
    test_content = f'''"""
Integration tests for {tool_config['file']} with hybrid MCP connections.
"""

import pytest
import tempfile
import os
import sys
from unittest.mock import Mock, patch

sys.path.append('src')
from dev_team.tools.{tool_config['file'].replace('.py', '')} import {tool_config['manager_name']}

class Test{tool_config['manager_name'].replace('MCP', '').replace('ConnectionManager', '')}:
    """Test hybrid MCP connection strategy for {tool_config['file']}."""
    
    def setup_method(self):
        """Set up test environment."""
        self.manager = {tool_config['manager_name']}()
        
    def test_aggregator_health_check(self):
        """Test aggregator health check."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            result = self.manager.check_aggregator_health()
            assert result is True
    
    def test_connection_fallback_chain(self):
        """Test the complete fallback chain."""
        with patch.object(self.manager, 'check_aggregator_health', return_value=False), \\
             patch.object(self.manager, 'start_individual_server', return_value=False):
            
            for server in {tool_config['servers']}:
                info = self.manager.get_connection_info(server)
                assert info['method'] == 'native'
                assert info['available'] is True
    
    def test_command_existence_check(self):
        """Test command existence checking."""
        result = self.manager._check_command_exists('python')
        assert result is True
        
        result = self.manager._check_command_exists('non-existent-command-xyz')
        assert result is False

if __name__ == "__main__":
    pytest.main([__file__])
'''
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"   ✅ Created integration test: {test_file}")

def main():
    """Main upgrade function."""
    print("🚀 Starting MCP Tools Hybrid Upgrade")
    print("=====================================")
    
    # Get project paths
    script_dir = Path(__file__).parent
    src_dir = script_dir / "src" / "dev_team" / "tools"
    test_dir = script_dir / "tests"
    
    # Ensure directories exist
    test_dir.mkdir(exist_ok=True)
    
    # Process each MCP tool
    for tool_config in MCP_TOOLS:
        try:
            upgrade_mcp_tool_file(tool_config, src_dir)
            create_integration_test(tool_config, test_dir)
            
        except Exception as e:
            print(f"   ❌ Error upgrading {tool_config['file']}: {e}")
            continue
    
    print(f"\\n🎉 Upgrade complete!")
    print("\\n📋 Next steps:")
    print("1. Review upgraded files for any syntax issues")
    print("2. Run integration tests to validate functionality")
    print("3. Update tool function implementations to use hybrid wrappers")
    print("4. Test with actual MCP servers when available")

if __name__ == "__main__":
    main()
