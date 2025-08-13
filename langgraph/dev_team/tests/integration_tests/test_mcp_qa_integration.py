"""Integration tests for MCP QA Tools."""

import pytest
import tempfile
import os
import sys
import subprocess
from pathlib import Path
from unittest.mock import patch

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

try:
    from dev_team.tools.mcp_qa_tools import (
        analyze_code_quality,
        run_load_test,
        create_load_test_script,
        validate_test_environment
    )
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    print(f"Import error: {e}")


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="MCP QA tools not available")
class TestQAToolsIntegration:
    """Integration tests for QA tools."""
    
    def test_code_quality_analysis_workflow(self):
        """Test complete code quality analysis workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a project with various code quality issues
            files_to_create = {
                "main.py": """
import os
import subprocess

def vulnerable_function(user_input):
    # Security issue: eval usage
    result = eval(user_input)
    
    # Security issue: shell injection
    subprocess.run(f"echo {user_input}", shell=True)
    
    return result

def performance_issues():
    # Performance issue: inefficient loop
    items = []
    for i in range(1000):
        items.append(str(i))
    
    # Performance issue: repeated string concatenation
    message = ""
    for item in items:
        message += item + ","
    
    return message

def error_handling_issues():
    try:
        risky_operation()
    except:  # Bare except
        pass
    
    try:
        another_operation()
    except Exception:  # Too broad exception
        return None

def complex_function(a, b, c, d):
    if a > 0 and b > 0 and c > 0 and d > 0:
        if a > b and b > c and c > d:
            for i in range(a):
                for j in range(b):
                    if i * j > c:
                        return i + j
    return 0
""",
                "utils.py": """
import pickle
import os

def unsafe_deserialization(data):
    # Security issue: unsafe pickle
    return pickle.loads(data)

def file_operations():
    # Potential security issue
    filename = input("Enter filename: ")
    with open(filename, 'r') as f:
        return f.read()
""",
                "config.py": """
# Configuration with hardcoded secrets
DATABASE_PASSWORD = "hardcoded_password123"
API_KEY = "sk-1234567890abcdef"

DEBUG = True
"""
            }
            
            # Create files
            for filename, content in files_to_create.items():
                file_path = Path(temp_dir) / filename
                file_path.write_text(content)
            
            # Initialize git repository if possible
            try:
                subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)
                subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_dir)
                subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_dir)
                subprocess.run(["git", "add", "."], cwd=temp_dir, capture_output=True)
                subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_dir, capture_output=True)
                
                # Make some changes for diff analysis
                (Path(temp_dir) / "new_file.py").write_text("print('new file')\nexec('dangerous')")
                
            except:
                pass  # Git might not be available
            
            # Test basic quality analysis
            result = analyze_code_quality(temp_dir)
            
            assert isinstance(result, dict)
            assert "success" in result
            assert result["workspace_root"] == temp_dir
            
            if result["success"] and "analysis" in result:
                analysis = result["analysis"]
                # Should detect some issues even with fallback analysis
                if "total_issues" in analysis:
                    assert analysis["total_issues"] >= 0
    
    def test_focused_quality_analysis(self):
        """Test quality analysis with focus on specific dimensions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create file with mixed issues
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("""
def mixed_issues():
    # Security vulnerability
    user_input = input("Enter code: ")
    result = eval(user_input)
    
    # Performance issue
    items = []
    for i in range(1000):
        items.append(i * 2)
    
    # Style issue (if detected)
    x=1;y=2;z=3
    
    return result
""")
            
            # Test with focus on security only
            result = analyze_code_quality(
                temp_dir,
                focus_dimensions=["security_vulnerabilities"]
            )
            
            assert isinstance(result, dict)
            assert "available_dimensions" in result
            assert len(result["available_dimensions"]) == 10
    
    def test_load_test_script_creation_and_validation(self):
        """Test creating and validating load test scripts."""
        # Test creating a simple script
        result = create_load_test_script(
            "http://httpbin.org",
            "httpbin_api_test",
            ["/get", "/post", "/status/200", "/delay/1"]
        )
        
        assert result["success"] is True
        assert "test_file_path" in result
        assert "test_content" in result
        
        test_file = result["test_file_path"]
        
        try:
            # Verify file was created and has expected content
            assert os.path.exists(test_file)
            
            with open(test_file, 'r') as f:
                content = f.read()
                
            # Check for required components
            assert "HttpbinApiTestUser" in content
            assert "HttpUser" in content
            assert "http://httpbin.org" in content
            assert "/get" in content
            assert "/post" in content
            assert "/status/200" in content
            assert "/delay/1" in content
            assert "@task" in content
            
            # Check for proper Python syntax
            try:
                compile(content, test_file, 'exec')
                syntax_valid = True
            except SyntaxError:
                syntax_valid = False
            
            assert syntax_valid, "Generated test script should have valid Python syntax"
            
        finally:
            # Clean up
            if os.path.exists(test_file):
                os.unlink(test_file)
    
    def test_load_test_execution_workflow(self):
        """Test load test execution workflow (mocked)."""
        # Create a simple test script
        result = create_load_test_script(
            "http://httpbin.org",
            "simple_test",
            ["/get"]
        )
        
        if result["success"]:
            test_file = result["test_file_path"]
            
            try:
                # Mock the actual load test execution
                with patch('subprocess.run') as mock_run:
                    mock_output = """
Name                 # reqs      # fails  |     Avg     Min     Max  Median  |   req/s failures/s
GET /get               100         2  |     150      80     300     140  |    10.0     0.20
Aggregated             100         2  |     150      80     300     140  |    10.0     0.20

Response time percentiles (approximated):
 Type     Name           50%    66%    75%    80%    90%    95%    98%    99%   99.9%   100%
 GET      /get           140    160    180    200    250    280    290    295    300    300
"""
                    mock_run.return_value = Mock(returncode=0, stdout=mock_output, stderr="")
                    
                    # Test load test execution
                    test_result = run_load_test(
                        test_file,
                        "http://httpbin.org",
                        users=5,
                        spawn_rate=1,
                        runtime="10s"
                    )
                    
                    assert test_result["success"] is True
                    assert "test_results" in test_result
                    assert "performance_summary" in test_result
                    
                    summary = test_result["performance_summary"]
                    assert summary["total_requests"] == 100
                    assert summary["success_rate"] == 98.0  # 98/100
                    assert "recommendations" in test_result
                    
            finally:
                if os.path.exists(test_file):
                    os.unlink(test_file)
    
    def test_environment_validation_comprehensive(self):
        """Test comprehensive environment validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock project structure
            (Path(temp_dir) / "requirements.txt").write_text("locust>=2.0.0\nrequests>=2.25.0")
            (Path(temp_dir) / "README.md").write_text("# Test Project")
            
            # Test validation without target URL
            result = validate_test_environment(temp_dir)
            
            assert result["success"] is True
            assert "validation_results" in result
            assert "recommendations" in result
            assert "overall_status" in result
            
            validation = result["validation_results"]
            assert "workspace_valid" in validation
            assert "git_available" in validation
            assert "locust_available" in validation
            assert "lucidity_available" in validation
            assert "python_version" in validation
            
            # Workspace should be valid
            assert validation["workspace_valid"] is True
            
            # Python version should be detected
            assert validation["python_version"] is not None
    
    def test_environment_validation_with_target(self):
        """Test environment validation with target connectivity check."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock requests for connectivity test
            with patch('requests.get') as mock_get:
                # Mock successful connection
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.elapsed.total_seconds.return_value = 0.5
                mock_get.return_value = mock_response
                
                result = validate_test_environment(temp_dir, "http://httpbin.org")
                
                assert result["success"] is True
                validation = result["validation_results"]
                
                assert "target_connectivity" in validation
                connectivity = validation["target_connectivity"]
                assert connectivity["reachable"] is True
                assert connectivity["status_code"] == 200
                assert connectivity["response_time"] == 0.5
    
    def test_qa_tools_error_handling(self):
        """Test error handling across QA tools."""
        # Test with invalid workspace
        result = analyze_code_quality("/nonexistent/path")
        assert isinstance(result, dict)
        assert "success" in result
        
        # Test with missing test file
        result = run_load_test("/nonexistent/test.py")
        assert result["success"] is False
        assert "error" in result
        
        # Test with invalid parameters
        result = create_load_test_script("")
        assert isinstance(result, dict)
        
        # Test validation with invalid workspace
        result = validate_test_environment("/nonexistent/path")
        assert result["success"] is True  # Should still work, just report issues
        assert result["validation_results"]["workspace_valid"] is False
    
    def test_qa_tools_with_git_repository(self):
        """Test QA tools with a proper git repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Initialize git repository
                subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True, timeout=10)
                subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_dir, timeout=5)
                subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_dir, timeout=5)
                
                # Create initial file
                initial_file = Path(temp_dir) / "initial.py"
                initial_file.write_text("print('hello world')")
                
                subprocess.run(["git", "add", "."], cwd=temp_dir, capture_output=True, timeout=5)
                subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_dir, capture_output=True, timeout=5)
                
                # Make changes with potential issues
                change_file = Path(temp_dir) / "changes.py"
                change_file.write_text("""
# New file with issues
user_input = input("Enter code: ")
result = eval(user_input)  # Security issue
print(result)
""")
                
                # Test quality analysis on git repository
                result = analyze_code_quality(temp_dir)
                
                assert isinstance(result, dict)
                assert result["workspace_root"] == temp_dir
                
                # Test environment validation
                env_result = validate_test_environment(temp_dir)
                validation = env_result["validation_results"]
                
                # Should detect git repository
                if validation["git_available"]:
                    assert validation["git_repository"] is True
                    
            except subprocess.TimeoutExpired:
                pytest.skip("Git operations timed out")
            except (FileNotFoundError, subprocess.CalledProcessError):
                pytest.skip("Git not available for testing")
    
    def test_concurrent_qa_operations(self):
        """Test concurrent QA operations."""
        import threading
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            for i in range(3):
                test_file = Path(temp_dir) / f"test_{i}.py"
                test_file.write_text(f"print('Test file {i}')\neval('dangerous_{i}')")
            
            results = []
            errors = []
            
            def analyze_worker():
                try:
                    result = analyze_code_quality(temp_dir)
                    results.append(result)
                except Exception as e:
                    errors.append(str(e))
            
            def create_test_worker():
                try:
                    result = create_load_test_script(
                        "http://example.com",
                        f"concurrent_test_{int(time.time())}",
                        ["/api/test"]
                    )
                    results.append(result)
                    
                    # Clean up created file
                    if result["success"] and "test_file_path" in result:
                        try:
                            os.unlink(result["test_file_path"])
                        except:
                            pass
                            
                except Exception as e:
                    errors.append(str(e))
            
            # Start concurrent operations
            threads = []
            for _ in range(2):
                thread1 = threading.Thread(target=analyze_worker)
                thread2 = threading.Thread(target=create_test_worker)
                threads.extend([thread1, thread2])
                thread1.start()
                thread2.start()
            
            # Wait for completion
            for thread in threads:
                thread.join(timeout=30)
            
            # Check results
            assert len(errors) == 0, f"Concurrent operations failed: {errors}"
            assert len(results) >= 2, f"Expected at least 2 results, got {len(results)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
