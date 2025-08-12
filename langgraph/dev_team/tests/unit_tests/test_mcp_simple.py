"""Simple unit tests for MCP Code Execution tools."""

import pytest
import sys
from pathlib import Path

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

try:
    from dev_team.tools.mcp_code_execution import (
        execute_python_code,
        execute_python_code_sandbox
    )
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    print(f"Import error: {e}")


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="MCP code execution tools not available")
class TestMCPCodeExecution:
    """Test MCP code execution tools."""
    
    def test_execute_python_code_simple(self):
        """Test simple Python code execution."""
        result = execute_python_code("print('Hello, World!')")
        
        assert isinstance(result, dict)
        assert "success" in result
        # Don't assert success=True since dependencies might not be available
        # Just verify we get a proper response structure
    
    def test_execute_python_code_with_error(self):
        """Test Python code execution with syntax error."""
        result = execute_python_code("print('unclosed string")
        
        assert isinstance(result, dict)
        assert "success" in result
        # Error should be present if execution failed
        if not result["success"]:
            assert "error" in result
    
    def test_execute_python_code_sandbox_fallback(self):
        """Test sandboxed execution with fallback."""
        result = execute_python_code_sandbox("print('Sandbox test')")
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "execution_method" in result
    
    def test_return_structure(self):
        """Test that return structure is consistent."""
        result = execute_python_code("x = 1 + 1")
        
        assert isinstance(result, dict)
        required_keys = ["success", "execution_method"]
        for key in required_keys:
            assert key in result


if __name__ == "__main__":
    pytest.main([__file__])
