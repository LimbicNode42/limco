"""Simple working tests for MCP QA tools."""

import pytest
import sys
import tempfile
from pathlib import Path

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

def test_qa_tools_import():
    """Test that QA tools can be imported."""
    try:
        from dev_team.tools.mcp_qa_tools import (
            analyze_code_quality,
            run_load_test,
            create_load_test_script,
            validate_test_environment
        )
        
        # Check that tools are callable
        assert callable(analyze_code_quality)
        assert callable(run_load_test)
        assert callable(create_load_test_script)
        assert callable(validate_test_environment)
        
        print("✓ All QA tools imported successfully")
        
    except ImportError as e:
        pytest.skip(f"QA tools not available: {e}")

def test_create_load_test_script_basic():
    """Test basic load test script creation."""
    try:
        from dev_team.tools.mcp_qa_tools import create_load_test_script
        
        result = create_load_test_script.invoke({
            "target_url": "http://example.com",
            "test_name": "example_test", 
            "endpoints": ["/api/health", "/api/status"]
        })
        
        assert isinstance(result, dict)
        assert "success" in result
        
        if result["success"]:
            assert "test_content" in result
            assert "target_url" in result
            assert result["target_url"] == "http://example.com"
            
            # Check content includes expected elements
            content = result["test_content"]
            assert "ExampletestUser" in content
            assert "/api/health" in content
            assert "/api/status" in content
            assert "HttpUser" in content
            
            print("✓ Load test script creation works")
            
            # Clean up if file was created
            if "test_file_path" in result:
                try:
                    import os
                    os.unlink(result["test_file_path"])
                except:
                    pass
        
    except ImportError as e:
        pytest.skip(f"QA tools not available: {e}")

def test_validate_test_environment_basic():
    """Test basic environment validation."""
    try:
        from dev_team.tools.mcp_qa_tools import validate_test_environment
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = validate_test_environment.invoke({
            "workspace_root": temp_dir
        })
            
            assert isinstance(result, dict)
            assert "success" in result
            assert "validation_results" in result
            
            validation = result["validation_results"]
            assert "workspace_valid" in validation
            assert "python_version" in validation
            
            # Workspace should be valid since we created it
            assert validation["workspace_valid"] is True
            
            # Python version should be detected
            assert validation["python_version"] is not None
            
            print("✓ Environment validation works")
        
    except ImportError as e:
        pytest.skip(f"QA tools not available: {e}")

def test_analyze_code_quality_basic():
    """Test basic code quality analysis."""
    try:
        from dev_team.tools.mcp_qa_tools import analyze_code_quality
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple Python file
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("""
def example_function():
    print("Hello, World!")
    return 42

if __name__ == "__main__":
    example_function()
""")
            
            result = analyze_code_quality.invoke({
            "workspace_root": temp_dir
        })
            
            assert isinstance(result, dict)
            assert "success" in result
            assert "workspace_root" in result
            assert result["workspace_root"] == temp_dir
            
            print("✓ Code quality analysis works")
        
    except ImportError as e:
        pytest.skip(f"QA tools not available: {e}")

def test_run_load_test_structure():
    """Test load test function structure."""
    try:
        from dev_team.tools.mcp_qa_tools import run_load_test
        
        # Test with non-existent file (should fail gracefully)
        result = run_load_test.invoke({
            "test_file": "/nonexistent/test.py"
        })
        
        assert isinstance(result, dict)
        assert "success" in result
        assert result["success"] is False
        assert "error" in result
        
        print("✓ Load test error handling works")
        
    except ImportError as e:
        pytest.skip(f"QA tools not available: {e}")

def test_qa_tool_availability():
    """Test checking QA tool availability."""
    try:
        from dev_team.tools.mcp_qa_tools import LucidityAnalyzer, LocustLoadTester
        
        # Test analyzer initialization
        analyzer = LucidityAnalyzer()
        assert hasattr(analyzer, 'is_available')
        assert hasattr(analyzer, 'QUALITY_DIMENSIONS')
        assert len(analyzer.QUALITY_DIMENSIONS) == 10
        
        # Test tester initialization
        tester = LocustLoadTester()
        assert hasattr(tester, 'is_available')
        
        print("✓ QA tool classes initialize correctly")
        
    except ImportError as e:
        pytest.skip(f"QA tools not available: {e}")

def test_quality_dimensions():
    """Test quality analysis dimensions."""
    try:
        from dev_team.tools.mcp_qa_tools import LucidityAnalyzer
        
        analyzer = LucidityAnalyzer()
        dimensions = analyzer.QUALITY_DIMENSIONS
        
        expected_dimensions = [
            "unnecessary_complexity",
            "poor_abstractions",
            "unintended_code_deletion", 
            "hallucinated_components",
            "style_inconsistencies",
            "security_vulnerabilities",
            "performance_issues",
            "code_duplication",
            "incomplete_error_handling",
            "test_coverage_gaps"
        ]
        
        for dimension in expected_dimensions:
            assert dimension in dimensions
        
        print("✓ All quality dimensions are available")
        
    except ImportError as e:
        pytest.skip(f"QA tools not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
