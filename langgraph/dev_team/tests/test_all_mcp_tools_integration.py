"""
Comprehensive integration test for all MCP tools with hybrid connection strategy
"""

import sys
import tempfile
import os
sys.path.append('src')

def test_file_operations():
    """Test file operations MCP tools."""
    print('='*60)
    print('TESTING FILE OPERATIONS MCP TOOLS')
    print('='*60)
    
    try:
        from dev_team.tools.mcp_file_operations import analyze_file_importance, read_file_efficiently
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file = os.path.join(tmpdir, 'important.py')
            with open(test_file, 'w') as f:
                f.write('''
class DatabaseManager:
    """Critical database management class."""
    def __init__(self):
        self.connection = None
    
    def connect(self):
        pass
    
    def execute_query(self, query):
        return []
''')
            
            # Test file importance analysis
            result = analyze_file_importance.invoke({
                'file_path': test_file,
                'workspace_root': tmpdir
            })
            
            print(f'✅ File Importance Analysis Success: {result.get("success", False)}')
            print(f'✅ Connection Method: {result.get("connection_method", "unknown")}')
            if result.get("success"):
                importance = result.get("importance_analysis", {})
                print(f'✅ Importance Score: {importance.get("importance_score", 0)}')
            
            # Test efficient file reading
            result2 = read_file_efficiently.invoke({
                'file_path': test_file,
                'max_size': 1000
            })
            
            print(f'✅ File Reading Success: {result2.get("success", False)}')
            print(f'✅ Connection Method: {result2.get("connection_method", "unknown")}')
            
            return result.get("success", False) and result2.get("success", False)
            
    except Exception as e:
        print(f'❌ File Operations Test Failed: {e}')
        return False

def test_code_execution():
    """Test code execution MCP tools."""
    print('\n' + '='*60)
    print('TESTING CODE EXECUTION MCP TOOLS')
    print('='*60)
    
    try:
        from dev_team.tools.mcp_code_execution import execute_python_code, execute_package_command
        
        # Test Python code execution
        result = execute_python_code.invoke({
            'code': 'print("Hello, MCP!")\nresult = 2 + 2\nprint(f"2 + 2 = {result}")',
            'timeout': 10
        })
        
        print(f'✅ Python Execution Success: {result.get("success", False)}')
        print(f'✅ Connection Method: {result.get("connection_method", "unknown")}')
        if result.get("success"):
            output = result.get("execution_result", {}).get("output", "")
            print(f'✅ Output Contains Hello: {"Hello, MCP!" in output}')
        
        # Test package command (safe command)
        result2 = execute_package_command.invoke({
            'command': 'python --version',
            'timeout': 5
        })
        
        print(f'✅ Package Command Success: {result2.get("success", False)}')
        print(f'✅ Connection Method: {result2.get("connection_method", "unknown")}')
        
        return result.get("success", False) and result2.get("success", False)
        
    except Exception as e:
        print(f'❌ Code Execution Test Failed: {e}')
        return False

def test_code_analysis():
    """Test code analysis MCP tools."""
    print('\n' + '='*60)
    print('TESTING CODE ANALYSIS MCP TOOLS')
    print('='*60)
    
    try:
        from dev_team.tools.mcp_code_analysis import analyze_code_structure, understand_code_context
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test code file
            test_file = os.path.join(tmpdir, 'sample.py')
            with open(test_file, 'w') as f:
                f.write('''
def fibonacci(n):
    """Calculate fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

class Calculator:
    def add(self, a, b):
        return a + b
    
    def multiply(self, a, b):
        return a * b
''')
            
            # Test code structure analysis
            result = analyze_code_structure.invoke({
                'file_path': test_file
            })
            
            print(f'✅ Code Structure Analysis Success: {result.get("success", False)}')
            print(f'✅ Connection Method: {result.get("connection_method", "unknown")}')
            if result.get("success"):
                structure = result.get("structure_analysis", {})
                print(f'✅ Functions Found: {len(structure.get("functions", []))}')
                print(f'✅ Classes Found: {len(structure.get("classes", []))}')
            
            # Test code context understanding
            result2 = understand_code_context.invoke({
                'code_snippet': 'def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)',
                'context': 'recursive algorithm'
            })
            
            print(f'✅ Code Context Understanding Success: {result2.get("success", False)}')
            print(f'✅ Connection Method: {result2.get("connection_method", "unknown")}')
            
            return result.get("success", False) and result2.get("success", False)
            
    except Exception as e:
        print(f'❌ Code Analysis Test Failed: {e}')
        return False

def test_qa_tools():
    """Test QA MCP tools (already validated)."""
    print('\n' + '='*60)
    print('TESTING QA MCP TOOLS (ALREADY VALIDATED)')
    print('='*60)
    
    try:
        from dev_team.tools.mcp_qa_tools import analyze_code_quality
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file with issues
            test_file = os.path.join(tmpdir, 'test.py')
            with open(test_file, 'w') as f:
                f.write('''
import subprocess
def risky():
    subprocess.run("ls", shell=True)
    try:
        eval("1+1")
    except:
        pass
''')
            
            result = analyze_code_quality.invoke({'workspace_root': tmpdir})
            
            print(f'✅ QA Analysis Success: {result.get("success", False)}')
            print(f'✅ Connection Method: {result.get("connection_method", "unknown")}')
            print(f'✅ Issues Found: {len(result.get("analysis", {}).get("issues", []))}')
            
            return result.get("success", False)
            
    except Exception as e:
        print(f'❌ QA Tools Test Failed: {e}')
        return False

def test_connection_managers():
    """Test that all MCP tools have proper connection managers."""
    print('\n' + '='*60)
    print('TESTING MCP CONNECTION MANAGERS')
    print('='*60)
    
    try:
        # Import connection managers from each module
        from dev_team.tools.mcp_file_operations import MCPConnectionManager as FileMCP
        from dev_team.tools.mcp_code_execution import MCPConnectionManager as ExecMCP  
        from dev_team.tools.mcp_code_analysis import MCPConnectionManager as AnalysisMCP
        from dev_team.tools.mcp_qa_tools import MCPConnectionManager as QAMCP
        
        managers = [
            ("File Operations", FileMCP()),
            ("Code Execution", ExecMCP()),
            ("Code Analysis", AnalysisMCP()),
            ("QA Tools", QAMCP())
        ]
        
        all_working = True
        for name, manager in managers:
            # Test aggregator health check
            health = manager.check_aggregator_health()
            print(f'{name} - Aggregator Health: {health}')
            
            # Test connection info
            info = manager.get_connection_info('test')
            method = info.get("method", "unknown")
            available = info.get("available", False)
            
            print(f'{name} - Connection Method: {method}')
            print(f'{name} - Available: {available}')
            
            # All should fall back to native and be available
            if method != "native" or not available:
                all_working = False
        
        return all_working
        
    except Exception as e:
        print(f'❌ Connection Manager Test Failed: {e}')
        return False

def main():
    """Run all MCP tool validation tests."""
    print("COMPREHENSIVE MCP TOOLS VALIDATION")
    print("=" * 80)
    print("Testing hybrid connection strategy across all MCP tools...")
    
    tests = [
        ("File Operations", test_file_operations),
        ("Code Execution", test_code_execution),
        ("Code Analysis", test_code_analysis), 
        ("QA Tools", test_qa_tools),
        ("Connection Managers", test_connection_managers)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result, None))
        except Exception as e:
            results.append((test_name, False, str(e)))
    
    # Summary
    print('\n' + '='*80)
    print('COMPREHENSIVE VALIDATION SUMMARY')
    print('='*80)
    
    passed = 0
    for test_name, success, error in results:
        if success:
            print(f'✅ {test_name}: PASSED')
            passed += 1
        else:
            print(f'❌ {test_name}: FAILED')
            if error:
                print(f'   Error: {error}')
    
    print(f'\nResults: {passed}/{len(tests)} test suites passed')
    
    if passed == len(tests):
        print('\n🎉 ALL MCP TOOLS SUCCESSFULLY UPGRADED!')
        print('   - Hybrid connection strategy implemented across all tools')
        print('   - Native fallbacks working for all MCP services')
        print('   - Production-ready with graceful degradation')
        return True
    else:
        print('\n⚠️  Some tests failed - check implementations')
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
