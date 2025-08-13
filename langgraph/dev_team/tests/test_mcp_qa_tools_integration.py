"""Integration tests for MCP QA Tools

These tests validate that the MCP QA tools work correctly across all connection methods:
- Aggregator connections
- Individual MCP server connections  
- Native Python fallbacks

Tests ensure MCP servers are ready for use and fallbacks work correctly.
"""

import pytest
import tempfile
import os
import shutil
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import requests

import sys
sys.path.append('src')

from dev_team.tools.mcp_qa_tools import (
    MCPConnectionManager, 
    LucidityAnalyzer,
    LocustLoadTester,
    analyze_code_quality,
    run_load_test,
    create_load_test_script,
    validate_test_environment
)


class TestMCPConnectionManager:
    """Test the MCP connection management and fallback strategy."""
    
    def setup_method(self):
        """Set up test environment."""
        self.manager = MCPConnectionManager()
        
    def test_aggregator_health_check_success(self):
        """Test successful aggregator health check."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            result = self.manager.check_aggregator_health()
            assert result is True
            mock_get.assert_called_once()
    
    def test_aggregator_health_check_failure(self):
        """Test failed aggregator health check."""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.RequestException("Connection failed")
            
            result = self.manager.check_aggregator_health()
            assert result is False
    
    def test_command_exists_check(self):
        """Test command existence checking."""
        # Test with a command that should exist
        result = self.manager._check_command_exists('python')
        assert result is True
        
        # Test with a command that shouldn't exist
        result = self.manager._check_command_exists('non-existent-command-xyz')
        assert result is False
    
    def test_connection_fallback_chain(self):
        """Test the complete fallback chain: aggregator -> individual -> native."""
        # Mock aggregator as unavailable
        with patch.object(self.manager, 'check_aggregator_health', return_value=False), \
             patch.object(self.manager, 'start_individual_server', return_value=False):
            
            # Test lucidity connection info
            info = self.manager.get_connection_info('lucidity')
            assert info['method'] == 'native'
            assert info['available'] is True  # Native should always be available
            assert info['url'] is None
            
            # Test locust connection info
            info = self.manager.get_connection_info('locust')
            assert info['method'] == 'native'
            assert info['available'] is True
    
    def test_individual_server_startup_command_not_found(self):
        """Test individual server startup when command doesn't exist."""
        with patch.object(self.manager, '_check_command_exists', return_value=False):
            result = self.manager.start_individual_server('lucidity')
            assert result is False
    
    def test_server_process_management(self):
        """Test server process tracking and cleanup."""
        # Mock successful server start
        with patch('subprocess.Popen') as mock_popen, \
             patch.object(self.manager, '_check_command_exists', return_value=True), \
             patch('requests.get') as mock_get:
            
            mock_process = Mock()
            mock_process.poll.return_value = None  # Process running
            mock_popen.return_value = mock_process
            
            # Mock health check success
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            result = self.manager.start_individual_server('lucidity')
            assert result is True
            assert 'lucidity' in self.manager.server_processes
            
            # Test cleanup
            self.manager.cleanup()
            mock_process.terminate.assert_called_once()


class TestLucidityAnalyzer:
    """Test Lucidity code analysis with all connection methods."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = LucidityAnalyzer()
        
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_python_file(self, content: str, filename: str = "test.py") -> str:
        """Create a test Python file with given content."""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path
    
    def test_native_analysis_basic_functionality(self):
        """Test native code analysis basic functionality."""
        # Create test files with various issues
        test_code = '''
import subprocess

def risky_function():
    # Security issue: shell=True
    result = subprocess.run("ls -la", shell=True)
    
    # Error handling issue: bare except
    try:
        eval("1+1")  # Another security issue
    except:
        pass
    
    return result

def very_long_function_with_many_parameters(param1, param2, param3, param4, param5, param6, param7, param8, param9):
    """This function has too many parameters and will be flagged."""
    if param1 and param2 and param3 and param4:
        if param5 or param6:
            while param7:
                for item in param8:
                    try:
                        if param9:
                            return "complex logic here that makes this function very long and complex with multiple nested control structures"
                    except ValueError:
                        continue
                    except TypeError:
                        break
    return None
'''
        self.create_test_python_file(test_code)
        
        # Test native analysis
        result = self.analyzer.analyze(self.temp_dir)
        
        assert result['success'] is True
        assert result['connection_method'] == 'native'
        assert result['analysis']['analysis_method'] == 'native'
        assert result['analysis']['total_files'] >= 1
        
        issues = result['analysis']['issues']
        assert len(issues) > 0
        
        # Check for specific issue types
        issue_types = [issue['dimension'] for issue in issues]
        assert 'security' in issue_types  # Should detect subprocess shell=True and eval
        assert 'maintainability' in issue_types  # Should detect bare except and function complexity
        
        # Verify metrics
        metrics = result['analysis']['metrics']
        assert 'code_complexity' in metrics
        assert 'maintainability_index' in metrics
        assert 'technical_debt_minutes' in metrics
        assert metrics['code_complexity'] > 1  # Should be complex due to nested structures
    
    def test_native_analysis_syntax_error_handling(self):
        """Test native analysis handles syntax errors gracefully."""
        # Create file with syntax error
        bad_code = '''
def broken_function(
    # Missing closing parenthesis and colon
    print("This will cause a syntax error")
'''
        self.create_test_python_file(bad_code, "syntax_error.py")
        
        result = self.analyzer.analyze(self.temp_dir)
        
        assert result['success'] is True
        assert result['connection_method'] == 'native'
        
        issues = result['analysis']['issues']
        syntax_errors = [issue for issue in issues if issue['dimension'] == 'syntax']
        assert len(syntax_errors) > 0
        assert 'syntax error' in syntax_errors[0]['description'].lower()
    
    def test_native_analysis_empty_workspace(self):
        """Test native analysis with empty workspace."""
        # Create empty directory
        empty_dir = os.path.join(self.temp_dir, "empty")
        os.makedirs(empty_dir)
        
        result = self.analyzer.analyze(empty_dir)
        
        assert result['success'] is True
        assert result['connection_method'] == 'native'
        assert result['analysis']['total_files'] == 0
        assert result['analysis']['total_lines'] == 0
        assert len(result['analysis']['issues']) == 0
    
    def test_native_analysis_specific_file(self):
        """Test native analysis of specific file."""
        test_code = '''
def clean_function():
    """A well-written function."""
    return "Hello, World!"
'''
        file_path = self.create_test_python_file(test_code, "clean.py")
        
        result = self.analyzer.analyze(self.temp_dir, target_path="clean.py")
        
        assert result['success'] is True
        assert result['connection_method'] == 'native'
        assert result['analysis']['total_files'] == 1
        # Should have fewer or no issues
        assert len(result['analysis']['issues']) == 0 or all(
            issue['severity'] == 'low' for issue in result['analysis']['issues']
        )
    
    @patch('requests.post')
    def test_mcp_server_analysis_fallback(self, mock_post):
        """Test MCP server analysis with fallback to native."""
        # Mock MCP server failure
        mock_post.side_effect = requests.RequestException("Connection failed")
        
        # Mock connection manager to think server is available
        with patch.object(self.analyzer.mcp_manager, 'get_connection_info') as mock_conn:
            mock_conn.return_value = {
                'available': True,
                'method': 'individual',
                'url': 'http://localhost:6969'
            }
            
            self.create_test_python_file("print('hello')")
            result = self.analyzer.analyze(self.temp_dir)
            
            # Should fallback to native when MCP fails
            assert result['success'] is True
            assert result['connection_method'] == 'native'


class TestLocustLoadTester:
    """Test Locust load testing with all connection methods."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.tester = LocustLoadTester()
        
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_locust_file(self) -> str:
        """Create a basic Locust test file."""
        content = '''
from locust import HttpUser, task

class QuickstartUser(HttpUser):
    @task
    def hello_world(self):
        self.client.get("/get")
'''
        file_path = os.path.join(self.temp_dir, "locustfile.py")
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path
    
    @patch('subprocess.run')
    def test_native_load_test_success(self, mock_run):
        """Test native load testing success scenario."""
        test_file = self.create_test_locust_file()
        
        # Mock successful Locust execution
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '''
Name                                                          # reqs      # fails |    Avg     Min     Max  Median  |   req/s  failures/s
---------------------------------------------------------------------------|-------|-------|-------|-------|-------|-------|--------
GET /get                                                          100         0 |    145      12    2500     120  |    3.33        0.00
---------------------------------------------------------------------------|-------|-------|-------|-------|-------|-------|--------
Aggregated                                                       100         0 |    145      12    2500     120  |    3.33        0.00

Response time percentiles (approximated)
Type     Name                                                              50%    66%    75%    80%    90%    95%    98%    99%  99.9% 99.99%   100%
--------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|
GET      /get                                                              120    130    140    150    200    300    500   1000   2500   2500   2500
--------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|
         Aggregated                                                        120    130    140    150    200    300    500   1000   2500   2500   2500
'''
        mock_run.return_value = mock_result
        
        result = self.tester.run_load_test(
            test_file=test_file,
            target_host="https://httpbin.org",
            users=10,
            spawn_rate=2,
            runtime="30s"
        )
        
        assert result['success'] is True
        assert result['connection_method'] == 'native'
        assert 'results' in result
        
        # Verify command was called correctly
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'locust' in args
        assert test_file in args
        assert 'https://httpbin.org' in args
    
    @patch('subprocess.run')
    def test_native_load_test_failure(self, mock_run):
        """Test native load testing failure scenario."""
        test_file = self.create_test_locust_file()
        
        # Mock failed Locust execution
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Error: Could not connect to target host"
        mock_run.return_value = mock_result
        
        result = self.tester.run_load_test(
            test_file=test_file,
            target_host="http://nonexistent.example.com",
            users=5,
            spawn_rate=1,
            runtime="10s"
        )
        
        assert result['success'] is False
        assert result['connection_method'] == 'native'
        assert 'error' in result
        assert 'Could not connect' in result['error']
    
    def test_native_test_script_creation(self):
        """Test native test script creation."""
        result = self.tester.create_test_script(
            target_url="https://api.example.com",
            test_name="api_test",
            endpoints=["/users", "/products", "/orders"]
        )
        
        assert result['success'] is True
        assert result['connection_method'] == 'native'
        assert 'script_path' in result
        assert 'script_content' in result
        
        # Verify script content
        script_content = result['script_content']
        assert 'from locust import HttpUser, task' in script_content
        assert 'https://api.example.com' in script_content
        assert '/users' in script_content
        assert '/products' in script_content
        assert '/orders' in script_content


class TestQAToolsIntegration:
    """Integration tests for the complete QA tools system."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_analyze_code_quality_tool_integration(self):
        """Test the analyze_code_quality tool end-to-end."""
        # Create test workspace with quality issues
        test_code = '''
import subprocess

def problematic_function():
    subprocess.run("rm -rf /", shell=True)  # Security issue
    try:
        eval("__import__('os').system('ls')")  # Security issue
    except:  # Maintainability issue
        pass
'''
        test_file = os.path.join(self.temp_dir, "problem.py")
        with open(test_file, 'w') as f:
            f.write(test_code)
        
        # Test the tool
        result = analyze_code_quality.invoke({
            'workspace_root': self.temp_dir
        })
        
        assert result['success'] is True
        assert result['connection_method'] == 'native'  # Will use native since no MCP servers
        
        analysis = result['analysis']
        assert analysis['total_files'] >= 1
        assert len(analysis['issues']) > 0
        
        # Should detect security issues
        security_issues = [
            issue for issue in analysis['issues'] 
            if issue['dimension'] == 'security'
        ]
        assert len(security_issues) >= 2  # shell=True and eval usage
    
    def test_run_load_test_tool_integration(self):
        """Test the run_load_test tool end-to-end."""
        # Create test Locust file
        test_content = '''
from locust import HttpUser, task

class TestUser(HttpUser):
    @task
    def test_endpoint(self):
        self.client.get("/get")
'''
        test_file = os.path.join(self.temp_dir, "test_load.py")
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        # Mock subprocess to avoid actual Locust execution
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Test completed successfully"
            mock_run.return_value = mock_result
            
            result = run_load_test.invoke({
                'test_file': test_file,
                'target_host': 'https://httpbin.org',
                'users': 5,
                'spawn_rate': 1,
                'runtime': '10s'
            })
            
            assert result['success'] is True
            assert result['connection_method'] == 'native'
    
    def test_mcp_readiness_validation(self):
        """Test MCP server readiness validation across all methods."""
        manager = MCPConnectionManager()
        
        # Test aggregator readiness
        aggregator_ready = manager.check_aggregator_health()
        print(f"Aggregator ready: {aggregator_ready}")
        
        # Test individual server readiness
        for server_name in ['lucidity', 'locust']:
            server_ready = manager.start_individual_server(server_name)
            print(f"{server_name} server ready: {server_ready}")
            
            # Get connection info (should fall back to native if servers not available)
            conn_info = manager.get_connection_info(server_name)
            print(f"{server_name} connection method: {conn_info['method']}")
            assert conn_info['available'] is True  # Native should always be available
        
        # Test cleanup
        manager.cleanup()
    
    def test_connection_method_reporting(self):
        """Test that all tools correctly report their connection method."""
        test_code = "print('hello world')"
        test_file = os.path.join(self.temp_dir, "simple.py")
        with open(test_file, 'w') as f:
            f.write(test_code)
        
        # Test code analysis
        result = analyze_code_quality.invoke({'workspace_root': self.temp_dir})
        assert 'connection_method' in result
        assert result['connection_method'] in ['aggregator', 'individual', 'native']
        
        # Test load testing (with mocked subprocess)
        locust_file = os.path.join(self.temp_dir, "locustfile.py")
        with open(locust_file, 'w') as f:
            f.write("from locust import HttpUser, task\nclass User(HttpUser):\n    @task\n    def t(self): pass")
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Success"
            mock_run.return_value = mock_result
            
            result = run_load_test.invoke({
                'test_file': locust_file,
                'target_host': 'http://localhost',
                'users': 1,
                'spawn_rate': 1,
                'runtime': '1s'
            })
            assert 'connection_method' in result
            assert result['connection_method'] in ['aggregator', 'individual', 'native']


if __name__ == "__main__":
    # Run tests manually for quick validation
    import traceback
    
    def run_test_suite():
        """Run all tests and report results."""
        test_classes = [
            TestMCPConnectionManager,
            TestLucidityAnalyzer, 
            TestLocustLoadTester,
            TestQAToolsIntegration
        ]
        
        total_tests = 0
        passed_tests = 0
        failed_tests = []
        
        for test_class in test_classes:
            print(f"\n{'='*60}")
            print(f"Running {test_class.__name__}")
            print('='*60)
            
            instance = test_class()
            
            # Get test methods
            test_methods = [
                method for method in dir(instance) 
                if method.startswith('test_')
            ]
            
            for test_method in test_methods:
                total_tests += 1
                print(f"\nRunning {test_method}...")
                
                try:
                    # Run setup if exists
                    if hasattr(instance, 'setup_method'):
                        instance.setup_method()
                    
                    # Run test
                    getattr(instance, test_method)()
                    
                    print(f"✅ {test_method} PASSED")
                    passed_tests += 1
                    
                except Exception as e:
                    print(f"❌ {test_method} FAILED: {e}")
                    traceback.print_exc()
                    failed_tests.append(f"{test_class.__name__}.{test_method}: {e}")
                
                finally:
                    # Run teardown if exists
                    if hasattr(instance, 'teardown_method'):
                        try:
                            instance.teardown_method()
                        except Exception:
                            pass
        
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print('='*60)
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {len(failed_tests)}")
        
        if failed_tests:
            print("\nFailed tests:")
            for failure in failed_tests:
                print(f"  - {failure}")
        
        print(f"\nSuccess rate: {(passed_tests/total_tests)*100:.1f}%")
        
        return len(failed_tests) == 0
    
    if run_test_suite():
        print("\n🎉 All tests passed!")
        exit(0)
    else:
        print("\n💥 Some tests failed!")
        exit(1)
