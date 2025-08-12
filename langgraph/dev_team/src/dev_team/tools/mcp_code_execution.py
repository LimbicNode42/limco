"""MCP Code Execution Tools

This module provides secure Python code execution capabilities using both
pydantic-ai/mcp-run-python for sandboxed execution and native subprocess for development.
"""

import asyncio
import subprocess
import tempfile
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import logging
from dataclasses import dataclass

from langchain_core.tools import tool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


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
    """Execute Python code in a secure environment.
    
    Args:
        python_code: Python code to execute
        use_mcp: If True, use MCP sandboxed execution; if False, use native subprocess
        timeout: Execution timeout in seconds (only for native execution)
        
    Returns:
        Dict with execution results including success, output, error, etc.
    """
    if use_mcp:
        # Use MCP sandboxed execution
        try:
            import asyncio
            
            async def run_mcp():
                async with get_mcp_executor() as executor:
                    return await executor.execute_code(python_code)
            
            # Check if we're in an event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, need to handle this differently
                result = asyncio.create_task(run_mcp())
                # For now, fall back to native execution in async contexts
                use_mcp = False
            except RuntimeError:
                # No event loop, we can run directly
                result = asyncio.run(run_mcp())
                
        except Exception as e:
            logger.warning(f"MCP execution failed, falling back to native: {e}")
            use_mcp = False
    
    if not use_mcp:
        # Use native subprocess execution
        executor = get_native_executor()
        result = executor.execute_code(python_code, timeout)
    
    return {
        "success": result.success,
        "output": result.output,
        "error": result.error,
        "return_value": result.return_value,
        "dependencies": result.dependencies,
        "execution_time": result.execution_time,
        "executor_type": "mcp" if use_mcp else "native"
    }


@tool
def execute_python_with_packages(
    python_code: str,
    packages: List[str],
    use_inline_metadata: bool = True,
    use_mcp: bool = True
) -> Dict[str, Any]:
    """Execute Python code with specific package dependencies.
    
    Args:
        python_code: Python code to execute
        packages: List of package names to install/use
        use_inline_metadata: If True, add PEP 723 metadata for packages
        use_mcp: If True, use MCP execution; if False, use native with pip install
        
    Returns:
        Dict with execution results
    """
    if use_inline_metadata and packages:
        # Add PEP 723 inline script metadata
        metadata = "# /// script\n"
        metadata += f"# dependencies = {packages}\n"
        metadata += "# ///\n\n"
        python_code = metadata + python_code
    
    if not use_mcp and packages:
        # Install packages using pip for native execution
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
                        "executor_type": "native"
                    }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Package installation failed: {str(e)}",
                "return_value": None,
                "dependencies": packages,
                "execution_time": None,
                "executor_type": "native"
            }
    
    return execute_python_secure(python_code, use_mcp=use_mcp)


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
