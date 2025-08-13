"""MCP Code Execution Tools

This module provides secure Python code execution capabilities using:
- pydantic-ai/mcp-run-python for sandboxed execution
- native subprocess for development

Implements hybrid connection strategy:
- Primary: MCP Aggregator connection (MCPX, mcgravity, etc.)
- Secondary: Individual MCP server startup
- Tertiary: Native Python implementations (always available)
"""

import asyncio
import subprocess
import tempfile
import os
import sys
import time
import threading
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import logging
from dataclasses import dataclass

from langchain_core.tools import tool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

# MCP Server Configuration - Hybrid Approach
# Primary: Connect to MCP Aggregator/Proxy
# Secondary: Start individual MCP servers
MCP_EXEC_CONFIG = {
    "aggregator": {
        "enabled": True,
        "url": os.getenv("MCP_AGGREGATOR_URL", "http://localhost:8080"),
        "timeout": 5,
        "python_executor_endpoint": "/python-executor",
        "deno_executor_endpoint": "/deno-executor"
    },
    "individual_servers": {
        "python-executor": {
            "port": int(os.getenv("PYTHON_EXECUTOR_MCP_PORT", "6974")),
            "host": "127.0.0.1",
            "start_command": ["mcp-run-python", "--transport", "sse"],
            "health_endpoint": "/health"
        },
        "deno-executor": {
            "port": int(os.getenv("DENO_EXECUTOR_MCP_PORT", "6975")),
            "host": "127.0.0.1", 
            "start_command": ["deno-mcp-executor", "--transport", "sse"],
            "health_endpoint": "/health"
        }
    },
    "fallback_native": True,
    "startup_timeout": 30,
    "health_check_interval": 10
}


class MCPExecConnectionManager:
    """Manages hybrid MCP connections for code execution - aggregator first, individual servers as fallback."""
    
    def __init__(self):
        self.config = MCP_EXEC_CONFIG
        self.aggregator_available = False
        self.individual_servers = {}
        self.server_processes = {}
        self._lock = threading.Lock()
        
    def check_aggregator_health(self) -> bool:
        """Check if MCP aggregator is available."""
        if not self.config["aggregator"]["enabled"]:
            return False
            
        try:
            url = self.config["aggregator"]["url"]
            timeout = self.config["aggregator"]["timeout"]
            response = requests.get(f"{url}/health", timeout=timeout)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Aggregator health check failed: {e}")
            return False
    
    def start_individual_server(self, server_name: str) -> bool:
        """Start an individual MCP server."""
        if server_name in self.server_processes:
            return True  # Already running
            
        config = self.config["individual_servers"].get(server_name)
        if not config:
            logger.error(f"No configuration found for server: {server_name}")
            return False
        
        # Check if command exists
        cmd_name = config["start_command"][0]
        if not self._check_command_exists(cmd_name):
            logger.warning(f"Command '{cmd_name}' not found, cannot start {server_name} server")
            return False
            
        try:
            # Build command with host and port
            cmd = config["start_command"] + [
                "--host", config["host"],
                "--port", str(config["port"])
            ]
            
            logger.info(f"Starting {server_name} MCP server: {' '.join(cmd)}")
            
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
                logger.info(f"{server_name} MCP server started successfully")
                return True
            else:
                logger.error(f"{server_name} MCP server failed health check")
                self.stop_individual_server(server_name)
                return False
                
        except Exception as e:
            logger.error(f"Failed to start {server_name} MCP server: {e}")
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
            url = f"http://{config['host']}:{config['port']}{config['health_endpoint']}"
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
                    logger.warning(f"Error stopping {server_name} server: {e}")
                finally:
                    del self.server_processes[server_name]
    
    def get_connection_info(self, server_type: str) -> Dict[str, Any]:
        """Get connection info for a server type (python-executor/deno-executor)."""
        # Try aggregator first
        if self.check_aggregator_health():
            aggregator_config = self.config["aggregator"]
            endpoint = aggregator_config.get(f"{server_type.replace('-', '_')}_endpoint", f"/{server_type}")
            return {
                "method": "aggregator",
                "url": f"{aggregator_config['url']}{endpoint}",
                "available": True
            }
        
        # Try individual server
        with self._lock:
            if not self.check_individual_server_health(server_type):
                if self.start_individual_server(server_type):
                    config = self.config["individual_servers"][server_type]
                    return {
                        "method": "individual",
                        "url": f"http://{config['host']}:{config['port']}",
                        "available": True
                    }
            else:
                config = self.config["individual_servers"][server_type]
                return {
                    "method": "individual",
                    "url": f"http://{config['host']}:{config['port']}",
                    "available": True
                }
        
        # Fallback to native - always available
        return {
            "method": "native",
            "url": None,
            "available": True  # Native implementations should always be available
        }
    
    def cleanup(self):
        """Clean up all running servers."""
        for server_name in list(self.server_processes.keys()):
            self.stop_individual_server(server_name)


# Global connection manager instance
_mcp_exec_manager = MCPExecConnectionManager()

# Alias for compatibility with test suite
MCPConnectionManager = MCPExecConnectionManager


@dataclass
class CodeExecutionResult:
    """Result of code execution."""
    success: bool
    output: str
    error: str
    return_value: Optional[Any] = None
    dependencies: Optional[List[str]] = None
    execution_time: Optional[float] = None


class MCPPythonExecutor:
    """Secure Python code execution using pydantic-ai/mcp-run-python."""
    
    def __init__(self):
        self.server_params = StdioServerParameters(
            command='deno',
            args=[
                'run',
                '-N',
                '-R=node_modules',
                '-W=node_modules',
                '--node-modules-dir=auto',
                'jsr:@pydantic/mcp-run-python',
                'stdio',
            ],
        )
        self._session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._client_context = stdio_client(self.server_params)
        self._read, self._write = await self._client_context.__aenter__()
        self._session = ClientSession(self._read, self._write)
        await self._session.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
        if self._client_context:
            await self._client_context.__aexit__(exc_type, exc_val, exc_tb)
    
    async def execute_code(self, python_code: str) -> CodeExecutionResult:
        """Execute Python code in secure sandbox.
        
        Args:
            python_code: Python code to execute
            
        Returns:
            CodeExecutionResult with execution details
        """
        try:
            result = await self._session.call_tool('run_python_code', {
                'python_code': python_code
            })
            
            # Parse the result content
            content = result.content[0].text
            
            # Extract status, output, return_value, dependencies from XML-like format
            success = '<status>success</status>' in content
            
            # Extract output
            output_start = content.find('<output>') + 8
            output_end = content.find('</output>')
            output = content[output_start:output_end] if output_start > 7 and output_end > -1 else ""
            
            # Extract error if present
            error_start = content.find('<error>')
            error = ""
            if error_start > -1:
                error_end = content.find('</error>')
                error = content[error_start + 7:error_end] if error_end > -1 else ""
            
            # Extract dependencies
            deps_start = content.find('<dependencies>')
            dependencies = None
            if deps_start > -1:
                deps_end = content.find('</dependencies>')
                deps_str = content[deps_start + 14:deps_end] if deps_end > -1 else ""
                try:
                    dependencies = eval(deps_str) if deps_str else None
                except:
                    dependencies = None
            
            # Extract return value
            return_value = None
            ret_start = content.find('<return_value>')
            if ret_start > -1:
                ret_end = content.find('</return_value>')
                ret_str = content[ret_start + 14:ret_end] if ret_end > -1 else ""
                try:
                    return_value = eval(ret_str) if ret_str else None
                except:
                    return_value = ret_str
            
            return CodeExecutionResult(
                success=success,
                output=output,
                error=error,
                return_value=return_value,
                dependencies=dependencies
            )
            
        except Exception as e:
            logger.error(f"MCP Python execution failed: {e}")
            return CodeExecutionResult(
                success=False,
                output="",
                error=f"Execution failed: {str(e)}"
            )


class NativeSubprocessExecutor:
    """Native Python subprocess execution for development."""
    
    def __init__(self, virtual_env_path: Optional[str] = None):
        """Initialize with optional virtual environment.
        
        Args:
            virtual_env_path: Path to Python virtual environment
        """
        self.virtual_env_path = virtual_env_path
        self.python_executable = self._get_python_executable()
    
    def _get_python_executable(self) -> str:
        """Get Python executable path."""
        if self.virtual_env_path:
            if os.name == 'nt':  # Windows
                return os.path.join(self.virtual_env_path, 'Scripts', 'python.exe')
            else:  # Unix-like
                return os.path.join(self.virtual_env_path, 'bin', 'python')
        return sys.executable
    
    def execute_code(self, python_code: str, timeout: int = 30) -> CodeExecutionResult:
        """Execute Python code using subprocess.
        
        Args:
            python_code: Python code to execute
            timeout: Execution timeout in seconds
            
        Returns:
            CodeExecutionResult with execution details
        """
        try:
            # Create temporary file for the code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(python_code)
                temp_file = f.name
            
            try:
                # Execute the code
                import time
                start_time = time.time()
                
                result = subprocess.run(
                    [self.python_executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=os.getcwd()
                )
                
                execution_time = time.time() - start_time
                
                return CodeExecutionResult(
                    success=result.returncode == 0,
                    output=result.stdout,
                    error=result.stderr,
                    execution_time=execution_time
                )
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file)
                except:
                    pass
                    
        except subprocess.TimeoutExpired:
            return CodeExecutionResult(
                success=False,
                output="",
                error=f"Code execution timed out after {timeout} seconds"
            )
        except Exception as e:
            logger.error(f"Native subprocess execution failed: {e}")
            return CodeExecutionResult(
                success=False,
                output="",
                error=f"Execution failed: {str(e)}"
            )


# Global executors
_mcp_executor = None
_native_executor = None


def get_mcp_executor() -> MCPPythonExecutor:
    """Get shared MCP executor instance."""
    global _mcp_executor
    if _mcp_executor is None:
        _mcp_executor = MCPPythonExecutor()
    return _mcp_executor


def get_native_executor() -> NativeSubprocessExecutor:
    """Get shared native executor instance."""
    global _native_executor
    if _native_executor is None:
        _native_executor = NativeSubprocessExecutor()
    return _native_executor


@tool
def execute_python_secure(
    python_code: str,
    use_mcp: bool = True,
    timeout: int = 30
) -> Dict[str, Any]:
    """Execute Python code in a secure environment using hybrid connection strategy.
    
    Execution order:
    1. MCP Aggregator (if available and use_mcp=True)
    2. Individual MCP servers (python-executor)
    3. Native subprocess execution (always available)
    
    Args:
        python_code: Python code to execute
        use_mcp: If True, attempt MCP execution before native fallback
        timeout: Execution timeout in seconds (only for native execution)
        
    Returns:
        Dict with execution results including success, output, error, etc.
    """
    execution_method = "unknown"
    result = None
    
    if use_mcp:
        # Try hybrid MCP connection strategy
        connection_info = _mcp_exec_manager.get_connection_info("python-executor")
        
        if connection_info["available"] and connection_info["method"] != "native":
            try:
                if connection_info["method"] == "aggregator":
                    # Use aggregator endpoint
                    execution_method = "mcp_aggregator"
                    result = _execute_via_aggregator(python_code, connection_info["url"])
                    
                elif connection_info["method"] == "individual":
                    # Use individual MCP server
                    execution_method = "mcp_individual"
                    result = _execute_via_individual_mcp(python_code, connection_info["url"])
                    
                if result and result.success:
                    return {
                        "success": result.success,
                        "output": result.output,
                        "error": result.error,
                        "return_value": result.return_value,
                        "dependencies": result.dependencies,
                        "execution_time": result.execution_time,
                        "executor_type": execution_method
                    }
                else:
                    logger.warning(f"MCP execution via {execution_method} failed, falling back to native")
                    
            except Exception as e:
                logger.warning(f"MCP execution via {connection_info['method']} failed: {e}, falling back to native")
    
    # Native fallback - always available
    execution_method = "native"
    try:
        executor = get_native_executor()
        result = executor.execute_code(python_code, timeout)
        
        return {
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "return_value": result.return_value,
            "dependencies": result.dependencies,
            "execution_time": result.execution_time,
            "executor_type": execution_method
        }
        
    except Exception as e:
        logger.error(f"All execution methods failed: {e}")
        return {
            "success": False,
            "output": "",
            "error": f"All execution methods failed: {str(e)}",
            "return_value": None,
            "dependencies": None,
            "execution_time": None,
            "executor_type": "failed"
        }


def _execute_via_aggregator(python_code: str, aggregator_url: str) -> CodeExecutionResult:
    """Execute Python code via MCP aggregator."""
    try:
        response = requests.post(
            aggregator_url,
            json={"python_code": python_code},
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            return CodeExecutionResult(
                success=data.get("success", False),
                output=data.get("output", ""),
                error=data.get("error", ""),
                return_value=data.get("return_value"),
                dependencies=data.get("dependencies"),
                execution_time=data.get("execution_time")
            )
        else:
            return CodeExecutionResult(
                success=False,
                output="",
                error=f"Aggregator returned status {response.status_code}: {response.text}"
            )
            
    except Exception as e:
        return CodeExecutionResult(
            success=False,
            output="",
            error=f"Aggregator request failed: {str(e)}"
        )


def _execute_via_individual_mcp(python_code: str, server_url: str) -> CodeExecutionResult:
    """Execute Python code via individual MCP server."""
    try:
        import asyncio
        
        async def run_mcp():
            async with get_mcp_executor() as executor:
                return await executor.execute_code(python_code)
        
        # Check if we're in an event loop
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, need to handle this differently
            # For now, return None to trigger fallback
            return None
        except RuntimeError:
            # No event loop, we can run directly
            return asyncio.run(run_mcp())
            
    except Exception as e:
        return CodeExecutionResult(
            success=False,
            output="",
            error=f"Individual MCP execution failed: {str(e)}"
        )


@tool
def execute_python_with_packages(
    python_code: str,
    packages: List[str],
    use_inline_metadata: bool = True,
    use_mcp: bool = True
) -> Dict[str, Any]:
    """Execute Python code with specific package dependencies using hybrid strategy.
    
    Execution order:
    1. MCP Aggregator (with PEP 723 metadata if supported)
    2. Individual MCP servers (python-executor with metadata)
    3. Native execution with pip install
    
    Args:
        python_code: Python code to execute
        packages: List of package names to install/use
        use_inline_metadata: If True, add PEP 723 metadata for packages
        use_mcp: If True, attempt MCP execution before native fallback
        
    Returns:
        Dict with execution results
    """
    if use_inline_metadata and packages:
        # Add PEP 723 inline script metadata
        metadata = "# /// script\n"
        metadata += f"# dependencies = {packages}\n"
        metadata += "# ///\n\n"
        python_code = metadata + python_code
    
    # Try MCP execution first (which should handle the metadata)
    result = execute_python_secure(python_code, use_mcp=use_mcp)
    
    # If MCP failed and we're using native execution, install packages first
    if not result["success"] and result["executor_type"] == "native" and packages:
        try:
            executor = get_native_executor()
            for package in packages:
                install_result = subprocess.run(
                    [executor.python_executable, '-m', 'pip', 'install', package],
                    capture_output=True,
                    text=True
                )
                if install_result.returncode != 0:
                    return {
                        "success": False,
                        "output": "",
                        "error": f"Failed to install package {package}: {install_result.stderr}",
                        "return_value": None,
                        "dependencies": packages,
                        "execution_time": None,
                        "executor_type": "native_with_packages"
                    }
            
            # Try execution again after installing packages
            result = execute_python_secure(python_code, use_mcp=False)  # Force native
            result["executor_type"] = "native_with_packages"
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Package installation failed: {str(e)}",
                "return_value": None,
                "dependencies": packages,
                "execution_time": None,
                "executor_type": "native_with_packages"
            }
    
    # Add package information to result
    result["dependencies"] = packages
    return result


@tool
def create_virtual_environment(
    env_name: str,
    packages: Optional[List[str]] = None,
    python_version: Optional[str] = None
) -> Dict[str, Any]:
    """Create a Python virtual environment for isolated execution.
    
    Args:
        env_name: Name of the virtual environment
        packages: Optional list of packages to install
        python_version: Optional Python version (e.g., "3.11")
        
    Returns:
        Dict with creation results and environment path
    """
    try:
        import venv
        
        # Create environment path
        venv_dir = Path.cwd() / "venvs" / env_name
        venv_dir.parent.mkdir(exist_ok=True)
        
        # Create virtual environment
        if python_version:
            # Try to use specific Python version
            python_exe = f"python{python_version}"
            result = subprocess.run(
                [python_exe, '-m', 'venv', str(venv_dir)],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                # Fall back to default Python
                venv.create(venv_dir, with_pip=True)
        else:
            venv.create(venv_dir, with_pip=True)
        
        # Install packages if provided
        if packages:
            if os.name == 'nt':  # Windows
                pip_exe = venv_dir / 'Scripts' / 'pip.exe'
            else:  # Unix-like
                pip_exe = venv_dir / 'bin' / 'pip'
            
            for package in packages:
                result = subprocess.run(
                    [str(pip_exe), 'install', package],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    return {
                        "success": False,
                        "error": f"Failed to install {package}: {result.stderr}",
                        "environment_path": str(venv_dir)
                    }
        
        return {
            "success": True,
            "message": f"Virtual environment '{env_name}' created successfully",
            "environment_path": str(venv_dir),
            "packages_installed": packages or []
        }
        
    except Exception as e:
        logger.error(f"Virtual environment creation failed: {e}")
        return {
            "success": False,
            "error": f"Failed to create virtual environment: {str(e)}",
            "environment_path": None
        }


@tool
def list_virtual_environments() -> Dict[str, Any]:
    """List available virtual environments.
    
    Returns:
        Dict with list of available environments
    """
    try:
        venvs_dir = Path.cwd() / "venvs"
        if not venvs_dir.exists():
            return {
                "success": True,
                "environments": [],
                "message": "No virtual environments directory found"
            }
        
        environments = []
        for env_dir in venvs_dir.iterdir():
            if env_dir.is_dir():
                # Check if it's a valid virtual environment
                if os.name == 'nt':  # Windows
                    python_exe = env_dir / 'Scripts' / 'python.exe'
                else:  # Unix-like
                    python_exe = env_dir / 'bin' / 'python'
                
                if python_exe.exists():
                    environments.append({
                        "name": env_dir.name,
                        "path": str(env_dir),
                        "python_executable": str(python_exe)
                    })
        
        return {
            "success": True,
            "environments": environments,
            "count": len(environments)
        }
        
    except Exception as e:
        logger.error(f"Failed to list virtual environments: {e}")
        return {
            "success": False,
            "error": f"Failed to list environments: {str(e)}",
            "environments": []
        }


# Export all tools
__all__ = [
    'MCPPythonExecutor',
    'NativeSubprocessExecutor', 
    'CodeExecutionResult',
    'execute_python_secure',
    'execute_python_with_packages',
    'create_virtual_environment',
    'list_virtual_environments'
]
