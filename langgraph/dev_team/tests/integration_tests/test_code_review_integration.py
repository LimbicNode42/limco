"""Integration tests for code review tools workflow."""

import os
import tempfile
import pytest
from unittest.mock import patch, Mock
from dev_team.tools import (
    run_static_analysis,
    run_security_scan,
    run_code_quality_check,
    request_copilot_review
)


class TestCodeReviewWorkflow:
    """Test the complete code review workflow integration."""
    
    def test_complete_code_review_workflow(self):
        """Test a complete code review workflow from start to finish."""
        # Sample code with various issues for testing
        test_code = '''
import os
import hashlib

# Hardcoded credentials - security issue
API_KEY = "sk-1234567890abcdef"
PASSWORD = "admin123"

def insecure_hash(data):
    """Hash data using MD5 - security vulnerability."""
    return hashlib.md5(data.encode()).hexdigest()

def eval_user_input(user_input):
    """Evaluate user input - major security risk."""
    return eval(user_input)

def poor_function_name(x,y,z):
    """Poor naming and no type hints."""
    return x+y+z

# TODO: This function needs refactoring
def complex_function(a, b, c, d, e, f, g, h):
    if a:
        if b:
            if c:
                if d:
                    if e:
                        if f:
                            return g + h
    return 0
'''
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_file = f.name
            
        try:
            # Step 1: Run comprehensive code quality check
            quality_result = run_code_quality_check.invoke({
                "file_path": temp_file,
                "include_metrics": True
            })
            
            # Verify quality check includes all sections
            assert "=== STATIC ANALYSIS ===" in quality_result
            assert "=== SECURITY SCAN ===" in quality_result
            assert "=== CODE METRICS ===" in quality_result
            assert "Total lines:" in quality_result
            assert "Comment ratio:" in quality_result
            
            # Step 2: Run detailed security scan
            security_result = run_security_scan.invoke({
                "file_path": temp_file,
                "scan_type": "all"
            })
            
            # Verify security issues are detected
            assert "Potential API Key found" in security_result
            assert "Potential Password found" in security_result
            
            # Step 3: Run static analysis
            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value = Mock(
                    stdout="************* Module test\nC0103: Constant name doesn't conform to UPPER_CASE naming style",
                    stderr="",
                    returncode=1
                )
                
                static_result = run_static_analysis.invoke({
                    "file_path": temp_file,
                    "tool": "pylint"
                })
                
                # Verify static analysis detects issues
                assert "Static Analysis Results" in static_result
                
            # Step 4: Get AI code review
            copilot_result = request_copilot_review.invoke({
                "code_content": test_code,
                "review_focus": "security"
            })
            
            # Verify AI review provides recommendations
            assert "🤖 **AI Code Review Report**" in copilot_result
            assert "Focus: Security" in copilot_result
            assert "🎯 **Recommendations**" in copilot_result
            assert "📊 **Overall Score**" in copilot_result
            
            # Step 5: Verify workflow completeness
            # All tools should provide actionable feedback
            all_results = [quality_result, security_result, static_result, copilot_result]
            for result in all_results:
                assert len(result) > 100  # Ensure substantial feedback
                assert not result.startswith("Error")  # No error messages
                
        finally:
            # Clean up
            os.unlink(temp_file)
            
    def test_clean_code_workflow(self):
        """Test workflow with clean, well-written code."""
        clean_code = '''
"""
A well-documented module for mathematical calculations.
"""

from typing import Union


def calculate_sum(first_number: int, second_number: int) -> int:
    """
    Calculate the sum of two integers.
    
    Args:
        first_number: The first integer to add
        second_number: The second integer to add
        
    Returns:
        The sum of the two input numbers
        
    Raises:
        TypeError: If inputs are not integers
    """
    if not isinstance(first_number, int) or not isinstance(second_number, int):
        raise TypeError("Both inputs must be integers")
    
    return first_number + second_number


def calculate_average(numbers: list[Union[int, float]]) -> float:
    """
    Calculate the average of a list of numbers.
    
    Args:
        numbers: A list of numeric values
        
    Returns:
        The arithmetic mean of the input numbers
        
    Raises:
        ValueError: If the list is empty
        TypeError: If inputs are not numeric
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    
    if not all(isinstance(num, (int, float)) for num in numbers):
        raise TypeError("All inputs must be numeric")
    
    return sum(numbers) / len(numbers)
'''
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(clean_code)
            temp_file = f.name
            
        try:
            # Test comprehensive quality check on clean code
            quality_result = run_code_quality_check.invoke({
                "file_path": temp_file,
                "include_metrics": True
            })
            
            # Should show good metrics
            assert "=== CODE METRICS ===" in quality_result
            assert "Comment ratio:" in quality_result
            
            # Test security scan on clean code
            security_result = run_security_scan.invoke({
                "file_path": temp_file,
                "scan_type": "secrets"
            })
            
            # Should find no security issues
            assert "No hardcoded secrets detected" in security_result
            
            # Test AI review on clean code
            copilot_result = request_copilot_review.invoke({
                "code_content": clean_code,
                "review_focus": "maintainability"
            })
            
            # Should provide positive feedback
            assert "🤖 **AI Code Review Report**" in copilot_result
            assert "Focus: Maintainability" in copilot_result
            
        finally:
            os.unlink(temp_file)
            
    def test_error_handling_workflow(self):
        """Test workflow error handling with problematic inputs."""
        
        # Test with non-existent file
        result = run_security_scan.invoke({
            "file_path": "/nonexistent/file.py",
            "scan_type": "secrets"
        })
        
        assert "Secret scan error" in result
        
        # Test with empty code review
        result = request_copilot_review.invoke({
            "code_content": "",
            "review_focus": "general"
        })
        
        assert "🤖 **AI Code Review Report**" in result
        assert "0 words, 0 lines" in result
        
    def test_tool_availability_workflow(self):
        """Test workflow when external tools are not available."""
        
        # Create a simple test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test(): pass")
            temp_file = f.name
            
        try:
            # Test when bandit is not available
            with patch('subprocess.run', side_effect=FileNotFoundError("bandit not found")):
                result = run_security_scan.invoke({
                    "file_path": temp_file,
                    "scan_type": "vulnerability"
                })
                
                assert "Bandit not installed" in result
                assert "pip install bandit" in result
                
            # Test when pylint is not available
            with patch('subprocess.run', side_effect=FileNotFoundError("pylint not found")):
                result = run_static_analysis.invoke({
                    "file_path": temp_file,
                    "tool": "pylint"
                })
                
                assert "not found" in result
                assert "pip install pylint" in result
                
        finally:
            os.unlink(temp_file)
            
    def test_performance_workflow(self):
        """Test workflow performance with realistic code sizes."""
        
        # Generate a larger code sample
        code_parts = []
        for i in range(50):
            code_parts.extend([
                f"def function_{i}():",
                f'    """Function number {i}."""',
                f"    return {i}",
                ""
            ])
        large_code = '\n'.join(code_parts)
        
        # Test AI review handles larger code efficiently
        result = request_copilot_review.invoke({
            "code_content": large_code,
            "review_focus": "performance"
        })
        
        assert "🤖 **AI Code Review Report**" in result
        assert "Focus: Performance" in result
        assert "199 lines" in result  # Should detect the larger size
        
    def test_multi_language_workflow(self):
        """Test workflow with different file types."""
        
        # Test JavaScript file detection
        js_result = run_static_analysis.invoke({
            "file_path": "test.js",
            "tool": "auto"
        })
        
        # Should fallback gracefully for JS
        assert "Basic code analysis" in js_result
        
        # Test TypeScript file detection
        ts_result = run_static_analysis.invoke({
            "file_path": "test.ts",
            "tool": "auto"
        })
        
        # Should fallback gracefully for TS
        assert "Basic code analysis" in ts_result
