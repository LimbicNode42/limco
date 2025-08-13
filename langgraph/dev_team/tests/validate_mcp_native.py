"""
Simple validation test for MCP QA Tools native implementations
"""

import sys
import tempfile
import os
sys.path.append('src')

def test_code_analysis():
    """Test native code analysis implementation."""
    print('='*60)
    print('TESTING CODE QUALITY ANALYSIS (NATIVE)')
    print('='*60)

    from dev_team.tools.mcp_qa_tools import analyze_code_quality

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test file with issues
        test_file = os.path.join(tmpdir, 'test.py')
        with open(test_file, 'w') as f:
            f.write('''
import subprocess

def risky_function():
    subprocess.run("ls -la", shell=True)
    try:
        eval("1+1")
    except:
        pass
''')

        result = analyze_code_quality.invoke({'workspace_root': tmpdir})
        success = result.get("success", False)
        method = result.get("connection_method", "unknown")
        issues = len(result.get("analysis", {}).get("issues", []))
        
        print(f'✅ Code Analysis Success: {success}')
        print(f'✅ Connection Method: {method}')
        print(f'✅ Issues Found: {issues}')
        
        return success and method == "native" and issues > 0

def test_connection_manager():
    """Test MCP connection manager."""
    print('\n' + '='*60)
    print('TESTING MCP CONNECTION MANAGER')
    print('='*60)

    from dev_team.tools.mcp_qa_tools import MCPConnectionManager

    manager = MCPConnectionManager()

    # Test aggregator health
    aggregator_health = manager.check_aggregator_health()
    print(f'Aggregator Health Check: {aggregator_health}')

    # Test connection info for services
    all_working = True
    for service in ['lucidity', 'locust']:
        info = manager.get_connection_info(service)
        method = info["method"]
        available = info["available"]
        
        print(f'{service} Connection Info:')
        print(f'  Method: {method}')
        print(f'  Available: {available}')
        
        # Native should always be available
        if method != "native" or not available:
            all_working = False
    
    return all_working

def test_load_testing():
    """Test native load testing implementation."""
    print('\n' + '='*60)
    print('TESTING LOAD TEST NATIVE IMPLEMENTATION')  
    print('='*60)

    from dev_team.tools.mcp_qa_tools import run_load_test

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('''
from locust import HttpUser, task

class TestUser(HttpUser):
    @task
    def test_get(self):
        self.client.get("/get")
''')
        locust_file = f.name

    try:
        # Test with minimal parameters 
        result = run_load_test.invoke({
            'test_file': locust_file,
            'target_host': 'https://httpbin.org',
            'users': 1,
            'spawn_rate': 1,
            'runtime': '2s',
            'headless': True
        })
        
        success = result.get("success", False)
        method = result.get("connection_method", "unknown")
        
        print(f'✅ Load Test Success: {success}')
        print(f'✅ Connection Method: {method}')
        
        if not success:
            print(f'⚠️  Load test error: {result.get("error", "Unknown")}')
            
        return success and method == "native"
        
    finally:
        os.unlink(locust_file)

def main():
    """Run all validation tests."""
    print("MCP QA TOOLS NATIVE IMPLEMENTATION VALIDATION")
    print("=" * 80)
    
    tests = [
        ("Code Analysis", test_code_analysis),
        ("Connection Manager", test_connection_manager), 
        ("Load Testing", test_load_testing)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result, None))
        except Exception as e:
            results.append((test_name, False, str(e)))
    
    # Summary
    print('\n' + '='*60)
    print('VALIDATION SUMMARY')
    print('='*60)
    
    passed = 0
    for test_name, success, error in results:
        if success:
            print(f'✅ {test_name}: PASSED')
            passed += 1
        else:
            print(f'❌ {test_name}: FAILED')
            if error:
                print(f'   Error: {error}')
    
    print(f'\nResults: {passed}/{len(tests)} tests passed')
    
    if passed == len(tests):
        print('\n🎉 All native MCP fallback methods are functioning correctly!')
        return True
    else:
        print('\n⚠️  Some tests failed - check implementation')
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
