import sys
import tempfile
import os
sys.path.append('src')

def test_file_operations():
    """Test file operations tools."""
    print('='*60)
    print('TESTING FILE OPERATIONS TOOLS')
    print('='*60)
    
    try:
        from dev_team.tools.mcp_file_operations import analyze_file_importance
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = os.path.join(tmpdir, 'important.py')
            with open(test_file, 'w') as f:
                f.write('class DatabaseManager:\n    def connect(self): pass')
            
            # Test with correct parameters
            result = analyze_file_importance.invoke({
                'project_path': tmpdir,
                'max_files': 10
            })
            
            print(f'✅ File Operations Success: {result.get("success", False)}')
            if result.get("success"):
                print(f'✅ Connection Method: {result.get("connection_method", "unknown")}')
            else:
                print(f'❌ Error: {result.get("error", "Unknown")}')
            
            return result.get("success", False)
            
    except Exception as e:
        print(f'❌ File Operations Error: {e}')
        return False

def test_code_execution():
    """Test code execution tools."""
    print('\n' + '='*60)
    print('TESTING CODE EXECUTION TOOLS')
    print('='*60)
    
    try:
        from dev_team.tools.mcp_code_execution import execute_python_secure
        
        # Test Python execution
        result = execute_python_secure.invoke({
            'python_code': 'print("Hello from MCP!")\nresult = 5 + 3\nprint(f"Result: {result}")',
            'timeout': 10
        })
        
        print(f'✅ Code Execution Success: {result.get("success", False)}')
        if result.get("success"):
            print(f'✅ Connection Method: {result.get("connection_method", "unknown")}')
            exec_result = result.get("execution_result", {})
            output = exec_result.get("output", "")
            if "Hello from MCP!" in output:
                print(f'✅ Output contains expected text')
        else:
            print(f'❌ Error: {result.get("error", "Unknown")}')
        
        return result.get("success", False)
        
    except Exception as e:
        print(f'❌ Code Execution Error: {e}')
        return False

def test_code_analysis():
    """Test code analysis tools.""" 
    print('\n' + '='*60)
    print('TESTING CODE ANALYSIS TOOLS')
    print('='*60)
    
    try:
        from dev_team.tools.mcp_code_analysis import analyze_python_file
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = os.path.join(tmpdir, 'sample.py')
            with open(test_file, 'w') as f:
                f.write('''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

class Calculator:
    def add(self, a, b):
        return a + b
''')
            
            result = analyze_python_file.invoke({
                'file_path': test_file
            })
            
            print(f'✅ Code Analysis Success: {result.get("success", False)}')
            if result.get("success"):
                print(f'✅ Connection Method: {result.get("connection_method", "unknown")}')
                analysis = result.get("analysis", {})
                functions = analysis.get("functions", [])
                classes = analysis.get("classes", [])
                print(f'✅ Functions found: {len(functions)}')
                print(f'✅ Classes found: {len(classes)}')
            else:
                print(f'❌ Error: {result.get("error", "Unknown")}')
            
            return result.get("success", False)
            
    except Exception as e:
        print(f'❌ Code Analysis Error: {e}')
        return False

def main():
    """Run focused tests on actual MCP tools."""
    print("FOCUSED MCP TOOLS TESTING")
    print("=" * 60)
    
    tests = [
        ("File Operations", test_file_operations),
        ("Code Execution", test_code_execution),
        ("Code Analysis", test_code_analysis)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f'❌ {test_name} Test Failed: {e}')
            results.append((test_name, False))
    
    # Summary
    print('\n' + '='*60)
    print('SUMMARY')
    print('='*60)
    
    passed = 0
    for test_name, success in results:
        if success:
            print(f'✅ {test_name}: PASSED')
            passed += 1
        else:
            print(f'❌ {test_name}: FAILED')
    
    print(f'\nResults: {passed}/{len(tests)} tests passed')
    
    if passed == len(tests):
        print('\n🎉 All MCP tools are working with hybrid connection strategy!')
    else:
        print('\n⚠️  Some tools need debugging')

if __name__ == "__main__":
    main()
