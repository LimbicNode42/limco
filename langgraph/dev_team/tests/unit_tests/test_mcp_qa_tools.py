"""Unit tests for MCP QA Tools."""

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
    from dev_team.tools.mcp_qa_tools import (
        LucidityAnalyzer,
        LocustLoadTester,
        CodeQualityIssue,
        LoadTestResult,
        QualityAnalysisResult,
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
class TestLucidityAnalyzer:
    """Test LucidityAnalyzer class."""
    
    def test_init(self):
        """Test LucidityAnalyzer initialization."""
        analyzer = LucidityAnalyzer()
        assert analyzer.server_url is not None
        assert analyzer.timeout == 30
        assert hasattr(analyzer, 'is_available')
        assert analyzer.QUALITY_DIMENSIONS is not None
        assert len(analyzer.QUALITY_DIMENSIONS) == 10
    
    @patch('subprocess.run')
    def test_check_availability_lucidity_available(self, mock_run):
        """Test availability check when Lucidity is available."""
        mock_run.return_value = Mock(returncode=0, stdout="Lucidity MCP server")
        
        analyzer = LucidityAnalyzer()
        result = analyzer._check_availability()
        
        # Should try to check for lucidity-mcp command
        assert isinstance(result, bool)
    
    @patch('subprocess.run')
    def test_check_availability_lucidity_not_available(self, mock_run):
        """Test availability check when Lucidity is not available."""
        mock_run.side_effect = FileNotFoundError()
        
        analyzer = LucidityAnalyzer()
        result = analyzer._check_availability()
        
        assert result is False
    
    @patch('requests.post')
    def test_analyze_changes_success(self, mock_post):
        """Test successful code analysis."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": {
                "issues": [
                    {
                        "dimension": "security_vulnerabilities",
                        "severity": "high",
                        "description": "SQL injection vulnerability"
                    }
                ],
                "total_issues": 1
            }
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        analyzer = LucidityAnalyzer()
        analyzer.is_available = True
        
        result = analyzer.analyze_changes("/path/to/project")
        
        assert result["success"] is True
        assert "analysis" in result
        assert result["method"] == "lucidity_mcp"
    
    def test_analyze_changes_unavailable(self):
        """Test analysis when Lucidity is unavailable."""
        analyzer = LucidityAnalyzer()
        analyzer.is_available = False
        
        result = analyzer.analyze_changes("/path/to/project")
        
        assert result["success"] is False
        assert "not available" in result["error"]
        assert result["fallback_used"] is True
    
    def test_analyze_with_git_diff(self):
        """Test git diff analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize git repo
            subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_dir)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_dir)
            
            # Create test file
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("print('hello')")
            
            subprocess.run(["git", "add", "."], cwd=temp_dir, capture_output=True)
            subprocess.run(["git", "commit", "-m", "initial"], cwd=temp_dir, capture_output=True)
            
            # Make changes
            test_file.write_text("print('hello')\neval('dangerous')")
            
            analyzer = LucidityAnalyzer()
            result = analyzer.analyze_with_git_diff(temp_dir)
            
            assert isinstance(result, dict)
            assert "success" in result
    
    def test_check_line_for_issues(self):
        """Test line-by-line issue detection."""
        analyzer = LucidityAnalyzer()
        
        # Test security issue
        issues = analyzer._check_line_for_issues("eval('dangerous')", "test.py", 1)
        assert len(issues) > 0
        assert any(issue.dimension == "security_vulnerabilities" for issue in issues)
        
        # Test safe line
        issues = analyzer._check_line_for_issues("print('hello')", "test.py", 1)
        # May or may not have issues depending on patterns


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="MCP QA tools not available")
class TestLocustLoadTester:
    """Test LocustLoadTester class."""
    
    def test_init(self):
        """Test LocustLoadTester initialization."""
        tester = LocustLoadTester()
        assert hasattr(tester, 'is_available')
    
    @patch('subprocess.run')
    def test_check_availability_locust_available(self, mock_run):
        """Test availability check when Locust is available."""
        mock_run.return_value = Mock(returncode=0, stdout="locust 2.8.6")
        
        tester = LocustLoadTester()
        result = tester._check_availability()
        
        assert result is True
    
    @patch('subprocess.run')
    def test_check_availability_locust_not_available(self, mock_run):
        """Test availability check when Locust is not available."""
        mock_run.side_effect = FileNotFoundError()
        
        tester = LocustLoadTester()
        result = tester._check_availability()
        
        assert result is False
    
    @patch('subprocess.run')
    def test_run_load_test_success(self, mock_run):
        """Test successful load test execution."""
        mock_output = """
Name                 # reqs      # fails  |     Avg     Min     Max  Median  |   req/s failures/s
GET /                   100         0  |     123      45     789     120  |    10.5     0.00
Aggregated             100         0  |     123      45     789     120  |    10.5     0.00
"""
        mock_run.return_value = Mock(returncode=0, stdout=mock_output, stderr="")
        
        tester = LocustLoadTester()
        tester.is_available = True
        
        result = tester.run_load_test("test.py")
        
        assert result.success is True
        assert result.total_requests > 0
        assert result.test_file == "test.py"
    
    @patch('subprocess.run')
    def test_run_load_test_failure(self, mock_run):
        """Test load test execution failure."""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="Error: test failed")
        
        tester = LocustLoadTester()
        tester.is_available = True
        
        result = tester.run_load_test("test.py")
        
        assert result.success is False
        assert "test failed" in result.error
    
    def test_run_load_test_unavailable(self):
        """Test load test when Locust is unavailable."""
        tester = LocustLoadTester()
        tester.is_available = False
        
        result = tester.run_load_test("test.py")
        
        assert result.success is False
        assert "not available" in result.error
    
    def test_create_simple_test(self):
        """Test creating a simple test file."""
        tester = LocustLoadTester()
        
        test_file = tester.create_simple_test("http://example.com", "example_test")
        
        assert os.path.exists(test_file)
        
        # Read and verify content
        with open(test_file, 'r') as f:
            content = f.read()
            assert "ExampleTestUser" in content
            assert "http://example.com" in content
            assert "HttpUser" in content
        
        # Clean up
        os.unlink(test_file)
    
    def test_parse_locust_output(self):
        """Test parsing Locust output."""
        tester = LocustLoadTester()
        
        sample_output = """
Name                 # reqs      # fails  |     Avg     Min     Max  Median  |   req/s failures/s
GET /api               150         5  |     200      50     500     180  |    15.0     0.50
GET /health             50         0  |      50      30     100      45  |     5.0     0.00
Aggregated             200         5  |     150      30     500     150  |    20.0     0.50
"""
        
        result = tester._parse_locust_output(sample_output, "test.py", "30s")
        
        assert result.success is True
        assert result.total_requests > 0
        assert result.failed_requests == 5
        assert result.successful_requests == 195


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="MCP QA tools not available")
class TestDataStructures:
    """Test data structure classes."""
    
    def test_code_quality_issue(self):
        """Test CodeQualityIssue dataclass."""
        issue = CodeQualityIssue(
            dimension="security_vulnerabilities",
            severity="high",
            file_path="test.py",
            line_number=10,
            description="SQL injection vulnerability",
            recommendation="Use parameterized queries",
            code_snippet="query = 'SELECT * FROM users WHERE id=' + user_id"
        )
        
        assert issue.dimension == "security_vulnerabilities"
        assert issue.severity == "high"
        assert issue.file_path == "test.py"
        assert issue.line_number == 10
        assert "SQL injection" in issue.description
    
    def test_load_test_result(self):
        """Test LoadTestResult dataclass."""
        result = LoadTestResult(
            test_file="test.py",
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            average_response_time=150.0,
            min_response_time=50.0,
            max_response_time=500.0,
            requests_per_second=10.5,
            duration="30s",
            success=True
        )
        
        assert result.test_file == "test.py"
        assert result.total_requests == 100
        assert result.successful_requests == 95
        assert result.success is True


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="MCP QA tools not available")
class TestToolFunctions:
    """Test the main tool functions."""
    
    @patch('dev_team.tools.mcp_qa_tools.get_lucidity_analyzer')
    def test_analyze_code_quality_tool(self, mock_get_analyzer):
        """Test analyze_code_quality tool function."""
        mock_analyzer = Mock()
        mock_analyzer.is_available = True
        mock_analyzer.analyze_changes.return_value = {
            "success": True,
            "analysis": {
                "total_issues": 2,
                "issues": [
                    {"dimension": "security_vulnerabilities", "severity": "high"},
                    {"dimension": "performance_issues", "severity": "medium"}
                ]
            },
            "method": "lucidity_mcp"
        }
        mock_get_analyzer.return_value = mock_analyzer
        
        result = analyze_code_quality("/path/to/project")
        
        assert result["success"] is True
        assert "analysis" in result
        assert result["workspace_root"] == "/path/to/project"
    
    @patch('dev_team.tools.mcp_qa_tools.get_lucidity_analyzer')
    def test_analyze_code_quality_with_focus(self, mock_get_analyzer):
        """Test analyze_code_quality with focus dimensions."""
        mock_analyzer = Mock()
        mock_analyzer.is_available = True
        mock_analyzer.analyze_changes.return_value = {
            "success": True,
            "analysis": {
                "total_issues": 3,
                "issues": [
                    {"dimension": "security_vulnerabilities", "severity": "high"},
                    {"dimension": "performance_issues", "severity": "medium"},
                    {"dimension": "style_inconsistencies", "severity": "low"}
                ]
            }
        }
        mock_get_analyzer.return_value = mock_analyzer
        
        result = analyze_code_quality(
            "/path/to/project", 
            focus_dimensions=["security_vulnerabilities"]
        )
        
        assert result["success"] is True
        # Should filter issues to only security ones
        analysis = result["analysis"]
        assert analysis["filtered_by_dimensions"] == ["security_vulnerabilities"]
    
    @patch('dev_team.tools.mcp_qa_tools.get_locust_tester')
    @patch('os.path.exists')
    def test_run_load_test_tool(self, mock_exists, mock_get_tester):
        """Test run_load_test tool function."""
        mock_exists.return_value = True
        
        mock_tester = Mock()
        mock_result = LoadTestResult(
            test_file="test.py",
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            average_response_time=150.0,
            min_response_time=50.0,
            max_response_time=500.0,
            requests_per_second=10.5,
            duration="30s",
            success=True
        )
        mock_tester.run_load_test.return_value = mock_result
        mock_get_tester.return_value = mock_tester
        
        result = run_load_test("test.py", "http://example.com")
        
        assert result["success"] is True
        assert "test_results" in result
        assert "performance_summary" in result
        assert result["performance_summary"]["success_rate"] == 95.0
    
    @patch('dev_team.tools.mcp_qa_tools.get_locust_tester')
    def test_create_load_test_script_tool(self, mock_get_tester):
        """Test create_load_test_script tool function."""
        mock_tester = Mock()
        mock_get_tester.return_value = mock_tester
        
        result = create_load_test_script(
            "http://api.example.com",
            "api_test",
            ["/users", "/orders", "/health"]
        )
        
        assert result["success"] is True
        assert "test_file_path" in result
        assert "test_content" in result
        assert "/users" in result["test_content"]
        assert "/orders" in result["test_content"]
        
        # Clean up if file was created
        if result["success"] and "test_file_path" in result:
            try:
                os.unlink(result["test_file_path"])
            except:
                pass
    
    @patch('subprocess.run')
    @patch('requests.get')
    def test_validate_test_environment_tool(self, mock_get, mock_run):
        """Test validate_test_environment tool function."""
        # Mock git availability
        mock_run.return_value = Mock(returncode=0, stdout="git version 2.34.1")
        
        # Mock target connectivity
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_get.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = validate_test_environment(temp_dir, "http://example.com")
            
            assert result["success"] is True
            assert "validation_results" in result
            assert "recommendations" in result
            assert result["validation_results"]["workspace_valid"] is True


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="MCP QA tools not available")
class TestErrorHandling:
    """Test error handling in QA tools."""
    
    def test_analyze_code_quality_invalid_workspace(self):
        """Test code quality analysis with invalid workspace."""
        result = analyze_code_quality("/nonexistent/path")
        
        # Should handle gracefully
        assert isinstance(result, dict)
        assert "success" in result
    
    def test_run_load_test_missing_file(self):
        """Test load test with missing test file."""
        result = run_load_test("/nonexistent/test.py", "http://example.com")
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    def test_create_load_test_script_invalid_params(self):
        """Test creating load test script with invalid parameters."""
        result = create_load_test_script("")
        
        # Should handle empty URL gracefully
        assert isinstance(result, dict)


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="MCP QA tools not available")
class TestIntegration:
    """Integration tests for QA tools."""
    
    def test_quality_analysis_integration(self):
        """Test complete quality analysis workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test Python file with issues
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("""
def unsafe_function(user_input):
    # Security vulnerability
    result = eval(user_input)
    
    # Performance issue
    items = []
    for i in range(100):
        items.append(str(i))
    
    # Error handling issue
    try:
        risky_operation()
    except:
        pass
    
    return result
""")
            
            # Initialize git if possible
            try:
                subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)
                subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_dir)
                subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_dir)
                subprocess.run(["git", "add", "."], cwd=temp_dir, capture_output=True)
                subprocess.run(["git", "commit", "-m", "test"], cwd=temp_dir, capture_output=True)
            except:
                pass  # Git not available
            
            # Test analysis
            result = analyze_code_quality(temp_dir)
            
            assert isinstance(result, dict)
            assert "success" in result
    
    def test_load_testing_integration(self):
        """Test complete load testing workflow."""
        # Create test script
        result = create_load_test_script(
            "http://httpbin.org",
            "httpbin_test",
            ["/get", "/status/200"]
        )
        
        if result["success"]:
            test_file = result["test_file_path"]
            
            try:
                # Validate the test file exists and has content
                assert os.path.exists(test_file)
                
                with open(test_file, 'r') as f:
                    content = f.read()
                    assert "HttpbinTestUser" in content
                    assert "/get" in content
                    assert "/status/200" in content
                
                # Note: We don't actually run the load test in CI
                # as it requires external connectivity
                
            finally:
                # Clean up
                if os.path.exists(test_file):
                    os.unlink(test_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
