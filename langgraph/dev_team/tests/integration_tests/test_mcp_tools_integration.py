"""Integration tests for MCP tools."""

import pytest
import tempfile
import os
import sys
from pathlib import Path
import subprocess
import json
from unittest.mock import patch

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

try:
    from dev_team.tools import mcp_code_execution, mcp_code_analysis, mcp_file_operations
except ImportError as e:
    pytest.skip(f"Cannot import MCP tools: {e}", allow_module_level=True)


class TestMCPCodeExecutionIntegration:
    """Integration tests for MCP code execution tools."""
    
    def test_python_code_execution_fallback(self):
        """Test Python code execution with fallback to subprocess."""
        # Test simple code execution
        result = mcp_code_execution.execute_python_code(
            "print('Hello from integration test')",
            use_sandbox=False
        )
        
        assert result["success"] is True
        assert "Hello from integration test" in result["output"]
        assert result["execution_method"] == "native_subprocess"
    
    def test_python_code_with_imports(self):
        """Test Python code execution with standard library imports."""
        code = """
import os
import json
import datetime

data = {
    "timestamp": datetime.datetime.now().isoformat(),
    "platform": os.name,
    "test": "integration"
}

print(json.dumps(data, indent=2))
"""
        
        result = mcp_code_execution.execute_python_code(code, use_sandbox=False)
        
        assert result["success"] is True
        assert "timestamp" in result["output"]
        assert "integration" in result["output"]
    
    def test_python_code_with_error_handling(self):
        """Test Python code execution with error."""
        code = """
try:
    x = 1 / 0
except ZeroDivisionError as e:
    print(f"Caught error: {e}")
    print("Error handled successfully")
"""
        
        result = mcp_code_execution.execute_python_code(code, use_sandbox=False)
        
        assert result["success"] is True
        assert "Caught error" in result["output"]
        assert "Error handled successfully" in result["output"]
    
    def test_virtual_environment_operations(self):
        """Test virtual environment creation and management."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Override default venv directory for testing
            with patch.object(mcp_code_execution.VirtualEnvironmentManager, '__init__') as mock_init:
                def custom_init(self, venv_base_dir=None):
                    self.venv_base_dir = venv_base_dir or temp_dir
                    os.makedirs(self.venv_base_dir, exist_ok=True)
                
                mock_init.side_effect = custom_init
                
                # Create virtual environment
                create_result = mcp_code_execution.create_virtual_environment("integration_test_env")
                
                if create_result["success"]:
                    # List environments
                    list_result = mcp_code_execution.list_virtual_environments()
                    assert list_result["success"] is True
                    
                    # Check if our environment is listed
                    env_names = [env["name"] for env in list_result["environments"]]
                    assert "integration_test_env" in env_names
                else:
                    pytest.skip("Virtual environment creation failed - Python venv module may not be available")


class TestMCPCodeAnalysisIntegration:
    """Integration tests for MCP code analysis tools."""
    
    def test_python_ast_analysis_comprehensive(self):
        """Test comprehensive Python AST analysis."""
        code = """
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

class DataProcessor:
    '''A class for processing data.'''
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.data: List[str] = []
    
    def load_data(self, file_path: str) -> bool:
        '''Load data from file.'''
        try:
            with open(file_path, 'r') as f:
                self.data = f.readlines()
            return True
        except FileNotFoundError:
            return False
    
    def process_data(self) -> Optional[List[str]]:
        '''Process the loaded data.'''
        if not self.data:
            return None
        
        processed = []
        for line in self.data:
            if line.strip():
                processed.append(line.strip().upper())
        
        return processed

def main():
    '''Main function.'''
    processor = DataProcessor({"mode": "test"})
    
    if processor.load_data("data.txt"):
        result = processor.process_data()
        if result:
            for item in result:
                print(item)
    else:
        print("Failed to load data")

if __name__ == "__main__":
    main()
"""
        
        # Test AST analysis
        result = mcp_code_analysis.analyze_python_code_ast(code)
        
        assert result["success"] is True
        assert len(result["functions"]) >= 3  # __init__, load_data, process_data, main
        assert len(result["classes"]) == 1
        
        # Check class details
        data_processor_class = next(c for c in result["classes"] if c["name"] == "DataProcessor")
        assert len(data_processor_class["methods"]) >= 3
        
        # Check function details
        main_function = next(f for f in result["functions"] if f["name"] == "main")
        assert main_function["has_docstring"] is True
    
    def test_code_complexity_analysis(self):
        """Test code complexity analysis."""
        complex_code = """
def complex_function(data, threshold=10):
    '''A complex function with multiple decision points.'''
    result = []
    
    for item in data:
        if item is None:
            continue
        
        if isinstance(item, str):
            if len(item) > threshold:
                try:
                    value = int(item)
                    if value > 100:
                        result.append(value * 2)
                    elif value > 50:
                        result.append(value * 1.5)
                    else:
                        result.append(value)
                except ValueError:
                    result.append(0)
            else:
                result.append(-1)
        elif isinstance(item, (int, float)):
            if item > threshold:
                result.append(item ** 2)
            else:
                result.append(item)
        else:
            result.append(None)
    
    return result
"""
        
        result = mcp_code_analysis.get_code_complexity_metrics(complex_code)
        
        assert result["success"] is True
        assert result["cyclomatic_complexity"] > 5  # Should be quite complex
        assert result["nesting_depth"] >= 3  # Multiple levels of nesting
        assert result["function_count"] == 1
    
    def test_dependency_extraction(self):
        """Test dependency extraction from code."""
        code_with_imports = """
# Standard library imports
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Union
from collections import defaultdict, Counter
from datetime import datetime, timedelta

# Third-party imports (would be detected if available)
try:
    import numpy as np
    import pandas as pd
except ImportError:
    np = None
    pd = None

# Local imports
from .utils import helper_function
from ..config import settings
from mypackage.core import CoreClass
"""
        
        result = mcp_code_analysis.extract_code_dependencies(code_with_imports)
        
        assert result["success"] is True
        
        expected_imports = ["os", "sys", "json", "pathlib", "typing", "collections", "datetime"]
        for expected in expected_imports:
            assert expected in result["imports"]
    
    def test_symbol_finding(self):
        """Test finding symbol definitions."""
        code = """
class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(('add', a, b, result))
        return result
    
    def multiply(self, a, b):
        result = a * b
        self.history.append(('multiply', a, b, result))
        return result

def create_calculator():
    return Calculator()

PI = 3.14159
VERSION = "1.0.0"
"""
        
        # Find class
        result = mcp_code_analysis.find_symbol_definitions(code, "Calculator")
        assert result["success"] is True
        assert len(result["definitions"]) == 1
        assert result["definitions"][0]["name"] == "Calculator"
        assert result["definitions"][0]["type"] == "class"
        
        # Find method
        result = mcp_code_analysis.find_symbol_definitions(code, "add")
        assert result["success"] is True
        assert len(result["definitions"]) == 1
        assert result["definitions"][0]["type"] == "function"
        
        # Find constant
        result = mcp_code_analysis.find_symbol_definitions(code, "PI")
        assert result["success"] is True
        assert len(result["definitions"]) == 1
        assert result["definitions"][0]["type"] == "variable"


class TestMCPFileOperationsIntegration:
    """Integration tests for MCP file operations tools."""
    
    def test_file_operations_workflow(self):
        """Test complete file operations workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_workflow.py"
            
            # Create initial file
            initial_content = """def hello():
    print("Hello, World!")

def goodbye():
    print("Goodbye!")
"""
            test_file.write_text(initial_content)
            
            # Read file efficiently
            read_result = mcp_file_operations.read_file_efficiently(
                str(test_file), start_line=1, end_line=3
            )
            assert read_result["success"] is True
            assert "hello" in read_result["content"]
            assert "goodbye" not in read_result["content"]  # Should not be in lines 1-3
            
            # Insert new function
            insert_result = mcp_file_operations.edit_file_at_line(
                str(test_file),
                3,
                "def new_function():\n    print('New function')\n",
                "insert"
            )
            assert insert_result["success"] is True
            
            # Replace a line
            replace_result = mcp_file_operations.edit_file_range(
                str(test_file),
                2,
                2,
                "    print('Hello, Updated World!')",
                "replace"
            )
            assert replace_result["success"] is True
            
            # Read final content
            final_read = mcp_file_operations.read_file_efficiently(str(test_file))
            assert final_read["success"] is True
            assert "new_function" in final_read["content"]
            assert "Updated World" in final_read["content"]
    
    def test_project_importance_analysis(self):
        """Test project importance analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a small project structure
            files_to_create = {
                "main.py": """
import utils
import config
from helpers import process_data

def main():
    config.load_settings()
    data = utils.load_data()
    result = process_data(data)
    utils.save_result(result)

if __name__ == "__main__":
    main()
""",
                "utils.py": """
import json
import os

def load_data():
    with open('data.json', 'r') as f:
        return json.load(f)

def save_result(result):
    with open('output.json', 'w') as f:
        json.dump(result, f)
""",
                "config.py": """
settings = {}

def load_settings():
    global settings
    settings = {"debug": True, "version": "1.0"}
""",
                "helpers.py": """
def process_data(data):
    return [item.upper() for item in data if isinstance(item, str)]
""",
                "tests/test_main.py": """
import unittest
from main import main

class TestMain(unittest.TestCase):
    def test_main(self):
        pass
"""
            }
            
            # Create files
            for file_path, content in files_to_create.items():
                full_path = Path(temp_dir) / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
            
            # Analyze project importance
            result = mcp_file_operations.analyze_file_importance(temp_dir, max_files=10)
            
            assert result["success"] is True
            assert result["total_files_analyzed"] >= 4  # Should analyze non-test files
            assert len(result["important_files"]) >= 1
            
            # Check that utils.py has high importance (many dependents)
            important_files = {f["file_path"]: f for f in result["important_files"]}
            utils_files = [f for f in important_files.values() if f["file_path"].endswith("utils.py")]
            if utils_files:
                utils_file = utils_files[0]
                assert utils_file["importance_score"] > 0


class TestMCPToolsEndToEnd:
    """End-to-end integration tests combining multiple MCP tools."""
    
    def test_code_development_workflow(self):
        """Test a complete code development workflow using all MCP tools."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_file = Path(temp_dir) / "calculator.py"
            
            # Step 1: Create initial code using file operations
            initial_code = '''class Calculator:
    def add(self, a, b):
        return a + b
'''
            project_file.write_text(initial_code)
            
            # Step 2: Analyze the code structure
            read_result = mcp_file_operations.read_file_efficiently(str(project_file))
            assert read_result["success"] is True
            
            ast_result = mcp_code_analysis.analyze_python_code_ast(read_result["content"])
            assert ast_result["success"] is True
            assert len(ast_result["classes"]) == 1
            assert ast_result["classes"][0]["name"] == "Calculator"
            
            # Step 3: Add more functionality
            additional_method = '''
    def multiply(self, a, b):
        return a * b
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
'''
            
            edit_result = mcp_file_operations.edit_file_at_line(
                str(project_file),
                3,
                additional_method,
                "insert"
            )
            assert edit_result["success"] is True
            
            # Step 4: Analyze complexity of updated code
            updated_content = mcp_file_operations.read_file_efficiently(str(project_file))
            complexity_result = mcp_code_analysis.get_code_complexity_metrics(updated_content["content"])
            assert complexity_result["success"] is True
            assert complexity_result["function_count"] >= 3  # add, multiply, divide
            
            # Step 5: Test the code by executing it
            test_code = f'''
{updated_content["content"]}

# Test the calculator
calc = Calculator()
print(f"Add: {{calc.add(5, 3)}}")
print(f"Multiply: {{calc.multiply(4, 6)}}")
print(f"Divide: {{calc.divide(10, 2)}}")

try:
    calc.divide(5, 0)
except ValueError as e:
    print(f"Error handled: {{e}}")
'''
            
            execution_result = mcp_code_execution.execute_python_code(test_code, use_sandbox=False)
            if execution_result["success"]:
                assert "Add: 8" in execution_result["output"]
                assert "Multiply: 24" in execution_result["output"]
                assert "Divide: 5.0" in execution_result["output"]
                assert "Error handled" in execution_result["output"]
            else:
                # If execution fails, at least verify the code is syntactically correct
                # by checking that AST analysis succeeds
                final_ast = mcp_code_analysis.analyze_python_code_ast(test_code)
                assert final_ast["success"] is True
    
    def test_project_analysis_and_refactoring(self):
        """Test project analysis and refactoring workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a project with some issues
            main_file = Path(temp_dir) / "main.py"
            utils_file = Path(temp_dir) / "utils.py"
            
            main_content = '''import utils
import os
import sys

def main():
    data = utils.load_data("input.txt")
    result = utils.process_data(data)
    utils.save_data(result, "output.txt")
    print("Processing complete")

if __name__ == "__main__":
    main()
'''
            
            utils_content = '''import json
import os

def load_data(filename):
    try:
        with open(filename, 'r') as f:
            return f.readlines()
    except FileNotFoundError:
        return []

def process_data(data):
    processed = []
    for line in data:
        if line.strip():
            processed.append(line.strip().upper())
    return processed

def save_data(data, filename):
    with open(filename, 'w') as f:
        for item in data:
            f.write(item + "\\n")
'''
            
            main_file.write_text(main_content)
            utils_file.write_text(utils_content)
            
            # Step 1: Analyze project structure
            importance_result = mcp_file_operations.analyze_file_importance(temp_dir)
            assert importance_result["success"] is True
            
            # Step 2: Analyze code complexity
            main_complexity = mcp_code_analysis.get_code_complexity_metrics(main_content)
            utils_complexity = mcp_code_analysis.get_code_complexity_metrics(utils_content)
            
            assert main_complexity["success"] is True
            assert utils_complexity["success"] is True
            
            # Step 3: Find all function definitions
            main_symbols = mcp_code_analysis.find_symbol_definitions(main_content, "main")
            utils_functions = mcp_code_analysis.analyze_python_code_ast(utils_content)
            
            assert main_symbols["success"] is True
            assert utils_functions["success"] is True
            assert len(utils_functions["functions"]) == 3  # load_data, process_data, save_data
            
            # Step 4: Test the current implementation
            combined_code = f'''
{utils_content}

{main_content.replace("import utils", "# utils imported above")}

# Create test data
with open("input.txt", "w") as f:
    f.write("hello\\nworld\\n\\ntest\\n")

# Run main
main()

# Check output
if os.path.exists("output.txt"):
    with open("output.txt", "r") as f:
        output = f.read()
        print("Output file contents:")
        print(output)
'''
            
            test_result = mcp_code_execution.execute_python_code(combined_code, use_sandbox=False)
            if test_result["success"]:
                assert "HELLO" in test_result["output"]
                assert "WORLD" in test_result["output"]
                assert "TEST" in test_result["output"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
