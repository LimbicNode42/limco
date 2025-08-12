"""Working unit tests for MCP Code Execution tools."""

import pytest
import sys
from pathlib import Path

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

def test_basic_code_execution():
    """Test basic Python code execution."""
    try:
        from dev_team.tools.mcp_code_execution import execute_python_secure
        
        # Test simple code execution
        result = execute_python_secure("print('Hello, World!')")
        
        assert isinstance(result, dict)
        assert result["success"] is True
        assert "Hello, World!" in result["output"]
        assert result["error"] == ""
        
    except ImportError as e:
        pytest.skip(f"MCP code execution tools not available: {e}")

def test_code_execution_with_error():
    """Test Python code execution with syntax error."""
    try:
        from dev_team.tools.mcp_code_execution import execute_python_secure
        
        # Test code with syntax error
        result = execute_python_secure("print('unclosed string")
        
        assert isinstance(result, dict)
        assert result["success"] is False
        assert result["error"] != ""
        
    except ImportError as e:
        pytest.skip(f"MCP code execution tools not available: {e}")

def test_code_execution_with_variables():
    """Test Python code execution with variables."""
    try:
        from dev_team.tools.mcp_code_execution import execute_python_secure
        
        code = """
x = 10
y = 20
result = x + y
print(f"Result: {result}")
"""
        
        result = execute_python_secure(code)
        
        assert isinstance(result, dict)
        assert result["success"] is True
        assert "Result: 30" in result["output"]
        
    except ImportError as e:
        pytest.skip(f"MCP code execution tools not available: {e}")

def test_code_execution_structure():
    """Test that code execution returns proper structure."""
    try:
        from dev_team.tools.mcp_code_execution import execute_python_secure
        
        result = execute_python_secure("x = 42")
        
        assert isinstance(result, dict)
        
        # Check required keys
        required_keys = ["success", "output", "error"]
        for key in required_keys:
            assert key in result
            
        # Check types
        assert isinstance(result["success"], bool)
        assert isinstance(result["output"], str)
        assert isinstance(result["error"], str)
        
    except ImportError as e:
        pytest.skip(f"MCP code execution tools not available: {e}")

def test_import_execution():
    """Test code execution with imports."""
    try:
        from dev_team.tools.mcp_code_execution import execute_python_secure
        
        code = """
import os
import json

data = {"test": "value", "number": 42}
print(json.dumps(data))
"""
        
        result = execute_python_secure(code)
        
        assert isinstance(result, dict)
        assert result["success"] is True
        assert "test" in result["output"]
        assert "42" in result["output"]
        
    except ImportError as e:
        pytest.skip(f"MCP code execution tools not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
