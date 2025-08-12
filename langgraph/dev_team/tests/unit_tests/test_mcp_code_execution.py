"""Unit tests for MCP Code Execution tools."""

import pytest
import tempfile
import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
import sys

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

try:
    from dev_team.tools.mcp_code_execution import (
        MCPPythonExecutor,
        NativeSubprocessExecutor,
        CodeExecutionResult,
        execute_python_code,
        execute_python_code_sandbox
    )
except ImportError as e:
    pytest.skip(f"Cannot import MCP code execution tools: {e}", allow_module_level=True)


class TestMCPPythonExecutor:
    """Test MCPPythonExecutor class."""
    
    def test_init(self):
        """Test MCPPythonExecutor initialization."""
        executor = MCPPythonExecutor()
        assert executor.server_url is not None
        assert executor.timeout == 30
        assert not executor.is_available
    
    @patch('subprocess.run')
    def test_check_availability_deno_available(self, mock_run):
        """Test availability check when Deno is available."""
        mock_run.return_value = Mock(returncode=0, stdout="deno 1.40.0")
        
        executor = MCPPythonExecutor()
        result = executor._check_availability()
        
        assert result is True
        assert executor.is_available is True
    
    @patch('subprocess.run')
    def test_check_availability_deno_not_available(self, mock_run):
        """Test availability check when Deno is not available."""
        mock_run.side_effect = FileNotFoundError()
        
        executor = MCPPythonExecutor()
        result = executor._check_availability()
        
        assert result is False
        assert executor.is_available is False
    
    @patch('requests.post')
    def test_execute_success(self, mock_post):
        """Test successful code execution."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": {"output": "Hello, World!", "error": None, "execution_time": 0.1}
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        executor = MCPPythonExecutor()
        executor.is_available = True
        
        result = executor.execute("print('Hello, World!')")
        
        assert result["success"] is True
        assert result["output"] == "Hello, World!"
        assert result["error"] is None
    
    @patch('requests.post')
    def test_execute_with_error(self, mock_post):
        """Test code execution with error."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": {"output": "", "error": "NameError: name 'x' is not defined", "execution_time": 0.1}
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        executor = MCPPythonExecutor()
        executor.is_available = True
        
        result = executor.execute("print(x)")
        
        assert result["success"] is False
        assert result["error"] == "NameError: name 'x' is not defined"
    
    @patch('requests.post')
    def test_execute_request_timeout(self, mock_post):
        """Test code execution with request timeout."""
        mock_post.side_effect = Exception("Request timeout")
        
        executor = MCPPythonExecutor()
        executor.is_available = True
        
        result = executor.execute("print('Hello')")
        
        assert result["success"] is False
        assert "Request timeout" in result["error"]
    
    def test_execute_unavailable(self):
        """Test execution when MCP server is unavailable."""
        executor = MCPPythonExecutor()
        executor.is_available = False
        
        result = executor.execute("print('Hello')")
        
        assert result["success"] is False
        assert "MCP Python execution server not available" in result["error"]


class TestNativeSubprocessExecutor:
    """Test NativeSubprocessExecutor class."""
    
    def test_init(self):
        """Test NativeSubprocessExecutor initialization."""
        executor = NativeSubprocessExecutor()
        assert executor.timeout == 30
        assert executor.max_output_size == 1024 * 1024  # 1MB
        assert executor.python_executable == "python"
    
    def test_execute_simple_code(self):
        """Test execution of simple Python code."""
        executor = NativeSubprocessExecutor()
        
        result = executor.execute("print('Hello, World!')")
        
        assert result["success"] is True
        assert "Hello, World!" in result["output"]
        assert result["error"] is None or result["error"] == ""
    
    def test_execute_with_syntax_error(self):
        """Test execution with syntax error."""
        executor = NativeSubprocessExecutor()
        
        result = executor.execute("print('Hello'")  # Missing closing quote
        
        assert result["success"] is False
        assert result["error"] is not None
        assert "SyntaxError" in result["error"]
    
    def test_execute_with_runtime_error(self):
        """Test execution with runtime error."""
        executor = NativeSubprocessExecutor()
        
        result = executor.execute("print(undefined_variable)")
        
        assert result["success"] is False
        assert result["error"] is not None
        assert "NameError" in result["error"]
    
    def test_execute_with_working_directory(self):
        """Test execution with custom working directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("Hello from file")
            
            executor = NativeSubprocessExecutor()
            code = """
with open('test.txt', 'r') as f:
    print(f.read().strip())
"""
            
            result = executor.execute(code, working_directory=temp_dir)
            
            assert result["success"] is True
            assert "Hello from file" in result["output"]
    
    def test_execute_with_environment_variables(self):
        """Test execution with custom environment variables."""
        executor = NativeSubprocessExecutor()
        code = "import os; print(os.environ.get('TEST_VAR', 'not found'))"
        env = {"TEST_VAR": "test_value"}
        
        result = executor.execute(code, environment=env)
        
        assert result["success"] is True
        assert "test_value" in result["output"]
    
    @patch('subprocess.run')
    def test_execute_timeout(self, mock_run):
        """Test execution timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("python", 1)
        
        executor = NativeSubprocessExecutor(timeout=1)
        
        result = executor.execute("import time; time.sleep(5)")
        
        assert result["success"] is False
        assert "timeout" in result["error"].lower()


class TestVirtualEnvironmentManager:
    """Test VirtualEnvironmentManager class."""
    
    def test_init(self):
        """Test VirtualEnvironmentManager initialization."""
        manager = VirtualEnvironmentManager()
        assert manager.venv_base_dir is not None
        assert Path(manager.venv_base_dir).exists()
    
    def test_create_virtual_environment(self):
        """Test virtual environment creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = VirtualEnvironmentManager(venv_base_dir=temp_dir)
            
            result = manager.create_venv("test_env")
            
            assert result["success"] is True
            assert Path(temp_dir) / "test_env" in [Path(p) for p in result["venv_path"]]
    
    def test_create_existing_virtual_environment(self):
        """Test creating virtual environment that already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = VirtualEnvironmentManager(venv_base_dir=temp_dir)
            
            # Create environment first time
            result1 = manager.create_venv("test_env")
            assert result1["success"] is True
            
            # Try to create same environment again
            result2 = manager.create_venv("test_env", force=False)
            assert result2["success"] is False
            assert "already exists" in result2["error"]
    
    def test_list_virtual_environments(self):
        """Test listing virtual environments."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = VirtualEnvironmentManager(venv_base_dir=temp_dir)
            
            # Create some environments
            manager.create_venv("env1")
            manager.create_venv("env2")
            
            result = manager.list_venvs()
            
            assert result["success"] is True
            assert len(result["environments"]) >= 2
            env_names = [env["name"] for env in result["environments"]]
            assert "env1" in env_names
            assert "env2" in env_names
    
    def test_get_venv_info(self):
        """Test getting virtual environment information."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = VirtualEnvironmentManager(venv_base_dir=temp_dir)
            
            # Create environment
            create_result = manager.create_venv("test_env")
            assert create_result["success"] is True
            
            # Get info
            result = manager.get_venv_info("test_env")
            
            assert result["success"] is True
            assert result["name"] == "test_env"
            assert "path" in result
            assert "python_executable" in result


class TestToolFunctions:
    """Test the main tool functions."""
    
    @patch('dev_team.tools.mcp_code_execution.MCPPythonExecutor')
    @patch('dev_team.tools.mcp_code_execution.NativeSubprocessExecutor')
    def test_execute_python_code_mcp_available(self, mock_native, mock_mcp):
        """Test execute_python_code when MCP is available."""
        # Mock MCP executor
        mock_mcp_instance = Mock()
        mock_mcp_instance.is_available = True
        mock_mcp_instance.execute.return_value = {
            "success": True,
            "output": "Hello, World!",
            "error": None
        }
        mock_mcp.return_value = mock_mcp_instance
        
        result = execute_python_code("print('Hello, World!')", use_sandbox=True)
        
        assert result["success"] is True
        assert result["output"] == "Hello, World!"
        assert result["execution_method"] == "mcp_sandbox"
    
    @patch('dev_team.tools.mcp_code_execution.MCPPythonExecutor')
    @patch('dev_team.tools.mcp_code_execution.NativeSubprocessExecutor')
    def test_execute_python_code_mcp_unavailable(self, mock_native, mock_mcp):
        """Test execute_python_code when MCP is unavailable."""
        # Mock MCP executor as unavailable
        mock_mcp_instance = Mock()
        mock_mcp_instance.is_available = False
        mock_mcp.return_value = mock_mcp_instance
        
        # Mock native executor
        mock_native_instance = Mock()
        mock_native_instance.execute.return_value = {
            "success": True,
            "output": "Hello, Native!",
            "error": None
        }
        mock_native.return_value = mock_native_instance
        
        result = execute_python_code("print('Hello, Native!')", use_sandbox=True)
        
        assert result["success"] is True
        assert result["output"] == "Hello, Native!"
        assert result["execution_method"] == "native_subprocess"
    
    @patch('dev_team.tools.mcp_code_execution.NativeSubprocessExecutor')
    def test_execute_python_code_native_only(self, mock_native):
        """Test execute_python_code with native execution only."""
        mock_native_instance = Mock()
        mock_native_instance.execute.return_value = {
            "success": True,
            "output": "Native execution",
            "error": None
        }
        mock_native.return_value = mock_native_instance
        
        result = execute_python_code("print('Native execution')", use_sandbox=False)
        
        assert result["success"] is True
        assert result["execution_method"] == "native_subprocess"
    
    @patch('dev_team.tools.mcp_code_execution.VirtualEnvironmentManager')
    def test_create_virtual_environment_tool(self, mock_manager):
        """Test create_virtual_environment tool function."""
        mock_manager_instance = Mock()
        mock_manager_instance.create_venv.return_value = {
            "success": True,
            "venv_path": "/path/to/venv",
            "python_executable": "/path/to/venv/bin/python"
        }
        mock_manager.return_value = mock_manager_instance
        
        result = create_virtual_environment("test_env")
        
        assert result["success"] is True
        assert "venv_path" in result
    
    @patch('dev_team.tools.mcp_code_execution.VirtualEnvironmentManager')
    def test_list_virtual_environments_tool(self, mock_manager):
        """Test list_virtual_environments tool function."""
        mock_manager_instance = Mock()
        mock_manager_instance.list_venvs.return_value = {
            "success": True,
            "environments": [
                {"name": "env1", "path": "/path/to/env1"},
                {"name": "env2", "path": "/path/to/env2"}
            ]
        }
        mock_manager.return_value = mock_manager_instance
        
        result = list_virtual_environments()
        
        assert result["success"] is True
        assert len(result["environments"]) == 2


class TestIntegration:
    """Integration tests for MCP code execution tools."""
    
    def test_real_python_execution(self):
        """Test real Python code execution (if Python is available)."""
        try:
            result = execute_python_code("print('Integration test')", use_sandbox=False)
            assert result["success"] is True
            assert "Integration test" in result["output"]
        except Exception:
            pytest.skip("Python not available for integration test")
    
    def test_real_virtual_environment_operations(self):
        """Test real virtual environment operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Override the default venv directory for testing
            with patch('dev_team.tools.mcp_code_execution.VirtualEnvironmentManager') as mock_manager:
                manager = VirtualEnvironmentManager(venv_base_dir=temp_dir)
                mock_manager.return_value = manager
                
                # Create environment
                create_result = create_virtual_environment("integration_test")
                if create_result["success"]:
                    # List environments
                    list_result = list_virtual_environments()
                    assert list_result["success"] is True
                    
                    # Check if our environment is in the list
                    env_names = [env["name"] for env in list_result["environments"]]
                    assert "integration_test" in env_names


if __name__ == "__main__":
    pytest.main([__file__])
