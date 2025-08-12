"""Comprehensive test coverage for MCP Code Execution tools."""

import pytest
import tempfile
import os
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch
import subprocess

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))


class TestCodeExecutionErrorHandling:
    """Test error handling and edge cases for code execution."""
    
    def test_execute_with_invalid_syntax(self):
        """Test execution with various syntax errors."""
        try:
            from dev_team.tools.mcp_code_execution import execute_python_secure
            
            invalid_codes = [
                "def incomplete_function(",  # Missing closing parenthesis
                "if x > 5:",  # Missing body
                "import",  # Incomplete import
                "print('unclosed string",  # Unclosed string
                "x = 1 +",  # Incomplete expression
            ]
            
            for code in invalid_codes:
                result = execute_python_secure.invoke({"python_code": code})
                assert result["success"] is False
                assert result["error"] != ""
                assert "SyntaxError" in result["error"] or "IndentationError" in result["error"]
                
        except ImportError:
            pytest.skip("MCP code execution not available")
    
    def test_execute_with_runtime_errors(self):
        """Test execution with various runtime errors."""
        try:
            from dev_team.tools.mcp_code_execution import execute_python_secure
            
            error_codes = [
                ("print(undefined_variable)", "NameError"),
                ("x = 1 / 0", "ZeroDivisionError"),
                ("x = [1, 2, 3]\nprint(x[10])", "IndexError"),
                ("d = {'a': 1}\nprint(d['b'])", "KeyError"),
                ("int('not_a_number')", "ValueError"),
            ]
            
            for code, expected_error in error_codes:
                result = execute_python_secure.invoke({"python_code": code})
                assert result["success"] is False
                assert expected_error in result["error"]
                
        except ImportError:
            pytest.skip("MCP code execution not available")
    
    def test_execute_with_infinite_loop_protection(self):
        """Test timeout protection against infinite loops."""
        try:
            from dev_team.tools.mcp_code_execution import execute_python_secure
            
            # This should timeout
            infinite_loop_code = """
import time
while True:
    time.sleep(0.1)
"""
            
            result = execute_python_secure.invoke({
                "python_code": infinite_loop_code,
                "timeout": 2  # 2 second timeout
            })
            
            # Should either timeout or be prevented
            assert result["success"] is False
            # Timeout error should be mentioned
            assert any(word in result["error"].lower() for word in ["timeout", "time", "limit"])
            
        except ImportError:
            pytest.skip("MCP code execution not available")
    
    def test_execute_with_large_output(self):
        """Test handling of large output."""
        try:
            from dev_team.tools.mcp_code_execution import execute_python_secure
            
            # Generate large output
            large_output_code = """
for i in range(1000):
    print(f"Line {i}: " + "x" * 100)
"""
            
            result = execute_python_secure.invoke({"python_code": large_output_code})
            
            # Should handle large output gracefully
            assert isinstance(result, dict)
            assert "output" in result
            # Output should be present but may be truncated
            assert len(result["output"]) > 0
            
        except ImportError:
            pytest.skip("MCP code execution not available")
    
    def test_execute_with_memory_intensive_code(self):
        """Test handling of memory-intensive operations."""
        try:
            from dev_team.tools.mcp_code_execution import execute_python_secure
            
            # Try to create large data structure
            memory_code = """
try:
    # Create moderately large list
    big_list = list(range(100000))
    print(f"Created list with {len(big_list)} elements")
    
    # Do some processing
    squares = [x*x for x in big_list[:1000]]
    print(f"Processed {len(squares)} squares")
    
except MemoryError:
    print("Memory limit reached")
except Exception as e:
    print(f"Error: {e}")
"""
            
            result = execute_python_secure.invoke({"python_code": memory_code})
            
            # Should complete successfully or handle memory limits gracefully
            assert isinstance(result, dict)
            if result["success"]:
                assert "Created list" in result["output"] or "Error:" in result["output"]
            
        except ImportError:
            pytest.skip("MCP code execution not available")


class TestVirtualEnvironmentManagement:
    """Test virtual environment management capabilities."""
    
    def test_virtual_environment_creation(self):
        """Test virtual environment creation tool."""
        try:
            from dev_team.tools.mcp_code_execution import create_virtual_environment
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Mock the venv creation for testing
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
                    
                    result = create_virtual_environment.invoke({
                        "name": "test_env",
                        "python_version": "3.11"
                    })
                    
                    assert isinstance(result, dict)
                    # Should attempt to create environment
                    
        except ImportError:
            pytest.skip("Virtual environment tools not available")
    
    def test_list_virtual_environments(self):
        """Test listing virtual environments."""
        try:
            from dev_team.tools.mcp_code_execution import list_virtual_environments
            
            result = list_virtual_environments.invoke({})
            
            assert isinstance(result, dict)
            assert "environments" in result or "success" in result
            
        except ImportError:
            pytest.skip("Virtual environment tools not available")


class TestCodeExecutionSecurity:
    """Test security aspects of code execution."""
    
    def test_file_system_access_restrictions(self):
        """Test that file system access is properly controlled."""
        try:
            from dev_team.tools.mcp_code_execution import execute_python_secure
            
            # Test various file operations
            file_operations = [
                "import os; print(os.getcwd())",  # Should work
                "open('/etc/passwd', 'r').read()",  # Should be restricted or fail
                "import subprocess; subprocess.run(['ls', '/'])",  # Should be restricted
            ]
            
            for code in file_operations:
                result = execute_python_secure.invoke({"python_code": code})
                assert isinstance(result, dict)
                # All should complete (either successfully or with controlled errors)
                
        except ImportError:
            pytest.skip("MCP code execution not available")
    
    def test_import_restrictions(self):
        """Test that dangerous imports are handled."""
        try:
            from dev_team.tools.mcp_code_execution import execute_python_secure
            
            # Test importing various modules
            import_tests = [
                "import os; print('os imported')",  # Standard library
                "import sys; print('sys imported')",  # Standard library
                "import json; print('json imported')",  # Standard library
                "import subprocess; print('subprocess imported')",  # Potentially dangerous
            ]
            
            for code in import_tests:
                result = execute_python_secure.invoke({"python_code": code})
                assert isinstance(result, dict)
                # Should handle all imports appropriately
                
        except ImportError:
            pytest.skip("MCP code execution not available")


class TestFileOperationsEdgeCases:
    """Test edge cases for file operations."""
    
    def test_read_nonexistent_file(self):
        """Test reading non-existent files."""
        try:
            from dev_team.tools.mcp_file_operations import read_file_efficiently
            
            result = read_file_efficiently.invoke({
                "file_path": "/nonexistent/path/file.txt",
                "start_line": 1,
                "end_line": 10
            })
            
            assert result["success"] is False
            assert "error" in result
            
        except ImportError:
            pytest.skip("File operations not available")
    
    def test_read_file_with_invalid_line_numbers(self):
        """Test reading files with invalid line ranges."""
        try:
            from dev_team.tools.mcp_file_operations import read_file_efficiently
            
            # Create a test file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("Line 1\nLine 2\nLine 3\n")
                test_file = f.name
            
            try:
                # Test various invalid ranges
                invalid_ranges = [
                    {"start_line": 0, "end_line": 5},  # Invalid start
                    {"start_line": 10, "end_line": 20},  # Beyond file length
                    {"start_line": 5, "end_line": 2},  # End before start
                ]
                
                for range_params in invalid_ranges:
                    result = read_file_efficiently.invoke({
                        "file_path": test_file,
                        **range_params
                    })
                    
                    # Should handle gracefully
                    assert isinstance(result, dict)
                    
            finally:
                os.unlink(test_file)
                
        except ImportError:
            pytest.skip("File operations not available")
    
    def test_edit_file_with_invalid_operations(self):
        """Test file editing with invalid operations."""
        try:
            from dev_team.tools.mcp_file_operations import edit_file_at_line
            
            # Create a test file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("Line 1\nLine 2\nLine 3\n")
                test_file = f.name
            
            try:
                # Test invalid operations
                invalid_ops = [
                    {"operation": "invalid_op"},
                    {"operation": "insert", "line_number": -1},
                    {"operation": "delete", "line_number": 1000},
                ]
                
                for op_params in invalid_ops:
                    result = edit_file_at_line.invoke({
                        "file_path": test_file,
                        "content": "test content",
                        **op_params
                    })
                    
                    # Should handle invalid operations gracefully
                    assert isinstance(result, dict)
                    
            finally:
                os.unlink(test_file)
                
        except ImportError:
            pytest.skip("File operations not available")
    
    def test_analyze_empty_project(self):
        """Test analyzing empty or minimal projects."""
        try:
            from dev_team.tools.mcp_file_operations import analyze_file_importance
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Empty directory
                result = analyze_file_importance.invoke({
                    "project_path": temp_dir,
                    "max_files": 10
                })
                
                assert isinstance(result, dict)
                if result["success"]:
                    assert result["total_files_analyzed"] == 0
                
        except ImportError:
            pytest.skip("File operations not available")


class TestCodeAnalysisValidation:
    """Test code analysis validation and edge cases."""
    
    def test_analyze_invalid_python_syntax(self):
        """Test analyzing Python code with syntax errors."""
        try:
            from dev_team.tools.mcp_code_analysis import analyze_python_file
            
            invalid_codes = [
                "def incomplete(",
                "if x > 5:",
                "import",
                "class Incomplete",
            ]
            
            for code in invalid_codes:
                result = analyze_python_file.invoke({
                    "file_path": "test.py",
                    "python_code": code
                })
                
                # Should handle invalid syntax gracefully
                assert isinstance(result, dict)
                
        except ImportError:
            pytest.skip("Code analysis not available")
    
    def test_analyze_large_codebase(self):
        """Test analyzing larger codebases."""
        try:
            from dev_team.tools.mcp_code_analysis import analyze_repository_structure
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create a larger project structure
                files_to_create = {}
                for i in range(20):
                    files_to_create[f"module_{i}.py"] = f"""
def function_{i}_1():
    return {i}

def function_{i}_2():
    import module_{(i+1) % 20}
    return module_{(i+1) % 20}.function_{(i+1) % 20}_1()

class Class_{i}:
    def method(self):
        return {i}
"""
                
                # Create files
                for filename, content in files_to_create.items():
                    file_path = Path(temp_dir) / filename
                    file_path.write_text(content)
                
                result = analyze_repository_structure.invoke({
                    "project_path": temp_dir,
                    "max_depth": 3
                })
                
                assert isinstance(result, dict)
                if result["success"]:
                    assert result["total_files"] >= 15  # Should find most files
                
        except ImportError:
            pytest.skip("Code analysis not available")
    
    def test_complexity_metrics_validation(self):
        """Test code complexity metrics with various code patterns."""
        try:
            from dev_team.tools.mcp_code_analysis import get_code_complexity_metrics
            
            test_cases = [
                ("def simple(): return 1", 1),  # Simple function
                ("""
def complex_function(x):
    if x > 0:
        if x > 10:
            for i in range(x):
                if i % 2 == 0:
                    return i
        else:
            return x
    else:
        return -1
""", 5),  # Complex function
                ("", 0),  # Empty code
                ("x = 1", 0),  # No functions
            ]
            
            for code, expected_min_complexity in test_cases:
                result = get_code_complexity_metrics.invoke({
                    "python_code": code
                })
                
                assert isinstance(result, dict)
                if result["success"]:
                    # Check that complexity makes sense
                    complexity = result.get("cyclomatic_complexity", 0)
                    assert complexity >= expected_min_complexity
                
        except ImportError:
            pytest.skip("Code analysis not available")


class TestConcurrentOperations:
    """Test concurrent operations and thread safety."""
    
    def test_concurrent_file_reading(self):
        """Test concurrent file reading operations."""
        try:
            from dev_team.tools.mcp_file_operations import read_file_efficiently
            import threading
            import time
            
            # Create test file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                for i in range(100):
                    f.write(f"Line {i}\n")
                test_file = f.name
            
            try:
                results = []
                errors = []
                
                def read_file_worker():
                    try:
                        result = read_file_efficiently.invoke({
                            "file_path": test_file,
                            "start_line": 1,
                            "end_line": 10
                        })
                        results.append(result)
                    except Exception as e:
                        errors.append(str(e))
                
                # Start multiple threads
                threads = []
                for _ in range(5):
                    thread = threading.Thread(target=read_file_worker)
                    threads.append(thread)
                    thread.start()
                
                # Wait for completion
                for thread in threads:
                    thread.join(timeout=10)
                
                # Check results
                assert len(errors) == 0, f"Errors in concurrent reading: {errors}"
                assert len(results) == 5, f"Expected 5 results, got {len(results)}"
                
                # All results should be successful
                for result in results:
                    assert result["success"] is True
                    
            finally:
                os.unlink(test_file)
                
        except ImportError:
            pytest.skip("File operations not available")
    
    def test_concurrent_code_execution(self):
        """Test concurrent code execution."""
        try:
            from dev_team.tools.mcp_code_execution import execute_python_secure
            import threading
            
            results = []
            errors = []
            
            def execute_worker(worker_id):
                try:
                    result = execute_python_secure.invoke({
                        "python_code": f"print('Worker {worker_id} executing')"
                    })
                    results.append((worker_id, result))
                except Exception as e:
                    errors.append((worker_id, str(e)))
            
            # Start multiple execution threads
            threads = []
            for i in range(3):
                thread = threading.Thread(target=execute_worker, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for completion
            for thread in threads:
                thread.join(timeout=15)
            
            # Check results
            assert len(errors) == 0, f"Errors in concurrent execution: {errors}"
            assert len(results) == 3, f"Expected 3 results, got {len(results)}"
            
        except ImportError:
            pytest.skip("Code execution not available")


class TestMemoryManagement:
    """Test memory management and caching behavior."""
    
    def test_file_cache_management(self):
        """Test file cache behavior."""
        try:
            from dev_team.tools.mcp_file_operations import read_file_efficiently, clear_file_cache
            
            # Create test file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("Test content for caching\n" * 100)
                test_file = f.name
            
            try:
                # Read file multiple times to populate cache
                for _ in range(3):
                    result = read_file_efficiently.invoke({
                        "file_path": test_file,
                        "start_line": 1,
                        "end_line": 50
                    })
                    assert result["success"] is True
                
                # Clear cache
                clear_result = clear_file_cache.invoke({"file_path": test_file})
                assert isinstance(clear_result, dict)
                
                # Read again after cache clear
                result = read_file_efficiently.invoke({
                    "file_path": test_file,
                    "start_line": 1,
                    "end_line": 50
                })
                assert result["success"] is True
                
            finally:
                os.unlink(test_file)
                
        except ImportError:
            pytest.skip("File operations not available")
    
    def test_clear_all_caches(self):
        """Test clearing all caches."""
        try:
            from dev_team.tools.mcp_file_operations import clear_file_cache
            
            # Clear all caches
            result = clear_file_cache.invoke({})
            
            assert isinstance(result, dict)
            assert result["success"] is True
            
        except ImportError:
            pytest.skip("File operations not available")


class TestIntegrationBetweenTools:
    """Test integration scenarios between different MCP tools."""
    
    def test_code_execution_and_analysis_integration(self):
        """Test using code execution results for analysis."""
        try:
            from dev_team.tools.mcp_code_execution import execute_python_secure
            from dev_team.tools.mcp_code_analysis import analyze_python_file
            
            # Execute code that generates more code
            generator_code = '''
def generated_function(x):
    """A dynamically generated function."""
    if x > 0:
        return x * 2
    else:
        return 0

print("Function generated successfully")
'''
            
            # Execute the generator
            exec_result = execute_python_secure.invoke({"python_code": generator_code})
            assert exec_result["success"] is True
            
            # Analyze the generated code
            analysis_result = analyze_python_file.invoke({
                "file_path": "generated.py",
                "python_code": generator_code
            })
            
            assert isinstance(analysis_result, dict)
            
        except ImportError:
            pytest.skip("Required tools not available")
    
    def test_file_analysis_and_editing_workflow(self):
        """Test workflow of analyzing files then editing them."""
        try:
            from dev_team.tools.mcp_file_operations import (
                read_file_efficiently, 
                analyze_file_importance,
                edit_file_at_line
            )
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create test files
                test_files = {
                    "main.py": "def main():\n    print('Hello')\n",
                    "utils.py": "def helper():\n    return True\n",
                    "config.py": "DEBUG = True\n"
                }
                
                for filename, content in test_files.items():
                    file_path = Path(temp_dir) / filename
                    file_path.write_text(content)
                
                # Analyze project importance
                importance_result = analyze_file_importance.invoke({
                    "project_path": temp_dir,
                    "max_files": 10
                })
                
                assert isinstance(importance_result, dict)
                
                # Read most important file
                if importance_result.get("success"):
                    main_file = str(Path(temp_dir) / "main.py")
                    read_result = read_file_efficiently.invoke({
                        "file_path": main_file,
                        "start_line": 1,
                        "end_line": 10
                    })
                    
                    assert read_result["success"] is True
                    
                    # Edit the file
                    edit_result = edit_file_at_line.invoke({
                        "file_path": main_file,
                        "line_number": 2,
                        "content": "    # Modified by integration test\n",
                        "operation": "insert"
                    })
                    
                    assert isinstance(edit_result, dict)
                
        except ImportError:
            pytest.skip("Required tools not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
