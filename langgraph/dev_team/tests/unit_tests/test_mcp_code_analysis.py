"""Unit tests for MCP Code Analysis tools."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
import ast

from dev_team.tools.mcp_code_analysis import (
    SerenaAnalyzer,
    RepoMapperAnalyzer,
    PythonASTAnalyzer,
    CodeComplexityMetrics,
    analyze_code_with_serena,
    analyze_repository_structure,
    analyze_python_code_ast,
    find_symbol_definitions,
    get_code_complexity_metrics,
    extract_code_dependencies
)


class TestSerenaAnalyzer:
    """Test SerenaAnalyzer class."""
    
    def test_init(self):
        """Test SerenaAnalyzer initialization."""
        analyzer = SerenaAnalyzer()
        assert analyzer.server_url is not None
        assert analyzer.timeout == 30
        assert not analyzer.is_available
    
    @patch('subprocess.run')
    def test_check_availability_serena_available(self, mock_run):
        """Test availability check when Serena is available."""
        mock_run.return_value = Mock(returncode=0, stdout="Serena MCP server")
        
        analyzer = SerenaAnalyzer()
        result = analyzer._check_availability()
        
        assert result is True
        assert analyzer.is_available is True
    
    @patch('subprocess.run')
    def test_check_availability_serena_not_available(self, mock_run):
        """Test availability check when Serena is not available."""
        mock_run.side_effect = FileNotFoundError()
        
        analyzer = SerenaAnalyzer()
        result = analyzer._check_availability()
        
        assert result is False
        assert analyzer.is_available is False
    
    @patch('requests.post')
    def test_analyze_code_success(self, mock_post):
        """Test successful code analysis."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": {
                "symbols": [{"name": "test_function", "type": "function", "line": 1}],
                "diagnostics": [],
                "references": []
            }
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        analyzer = SerenaAnalyzer()
        analyzer.is_available = True
        
        result = analyzer.analyze_code("def test_function(): pass", "test.py")
        
        assert result["success"] is True
        assert len(result["symbols"]) == 1
        assert result["symbols"][0]["name"] == "test_function"
    
    def test_analyze_code_unavailable(self):
        """Test code analysis when Serena is unavailable."""
        analyzer = SerenaAnalyzer()
        analyzer.is_available = False
        
        result = analyzer.analyze_code("def test(): pass", "test.py")
        
        assert result["success"] is False
        assert "Serena analyzer not available" in result["error"]


class TestRepoMapperAnalyzer:
    """Test RepoMapperAnalyzer class."""
    
    def test_init(self):
        """Test RepoMapperAnalyzer initialization."""
        analyzer = RepoMapperAnalyzer()
        assert analyzer.supported_extensions is not None
        assert '.py' in analyzer.supported_extensions
    
    def test_analyze_repository_structure(self):
        """Test repository structure analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            (Path(temp_dir) / "main.py").write_text("import utils\ndef main(): pass")
            (Path(temp_dir) / "utils.py").write_text("def helper(): pass")
            subdir = Path(temp_dir) / "subdir"
            subdir.mkdir()
            (subdir / "module.py").write_text("from utils import helper")
            
            analyzer = RepoMapperAnalyzer()
            result = analyzer.analyze_repository(temp_dir)
            
            assert result["success"] is True
            assert "files" in result
            assert len(result["files"]) >= 3
            assert "dependencies" in result
    
    def test_extract_file_imports(self):
        """Test file import extraction."""
        analyzer = RepoMapperAnalyzer()
        
        # Test Python imports
        python_code = """
import os
import sys
from pathlib import Path
from typing import Dict, List
from .local_module import function
"""
        imports = analyzer._extract_file_imports(python_code, "python")
        
        assert "os" in imports
        assert "sys" in imports
        assert "pathlib" in imports
        assert "typing" in imports
        assert "local_module" in imports
    
    def test_calculate_file_importance(self):
        """Test file importance calculation."""
        analyzer = RepoMapperAnalyzer()
        
        # Test with high importance file (many dependents)
        importance = analyzer._calculate_file_importance(2, 5, 100)  # deps, dependents, loc
        assert importance > 5.0
        
        # Test with low importance file
        importance = analyzer._calculate_file_importance(0, 0, 10)
        assert importance < 2.0


class TestPythonASTAnalyzer:
    """Test PythonASTAnalyzer class."""
    
    def test_init(self):
        """Test PythonASTAnalyzer initialization."""
        analyzer = PythonASTAnalyzer()
        assert analyzer is not None
    
    def test_analyze_python_code_simple(self):
        """Test analysis of simple Python code."""
        code = """
def test_function(x, y):
    '''A test function.'''
    if x > y:
        return x
    else:
        return y

class TestClass:
    def __init__(self):
        self.value = 42
    
    def method(self):
        return self.value
"""
        
        analyzer = PythonASTAnalyzer()
        result = analyzer.analyze_code(code)
        
        assert result["success"] is True
        assert len(result["functions"]) == 1
        assert len(result["classes"]) == 1
        assert result["functions"][0]["name"] == "test_function"
        assert result["classes"][0]["name"] == "TestClass"
    
    def test_find_symbol_definitions(self):
        """Test finding symbol definitions."""
        code = """
def target_function():
    pass

class TargetClass:
    def target_method(self):
        pass

target_variable = 42
"""
        
        analyzer = PythonASTAnalyzer()
        
        # Find function
        result = analyzer.find_symbol_definitions(code, "target_function")
        assert len(result) == 1
        assert result[0]["name"] == "target_function"
        assert result[0]["type"] == "function"
        
        # Find class
        result = analyzer.find_symbol_definitions(code, "TargetClass")
        assert len(result) == 1
        assert result[0]["name"] == "TargetClass"
        assert result[0]["type"] == "class"
        
        # Find variable
        result = analyzer.find_symbol_definitions(code, "target_variable")
        assert len(result) == 1
        assert result[0]["name"] == "target_variable"
        assert result[0]["type"] == "variable"
    
    def test_calculate_complexity_metrics(self):
        """Test complexity metrics calculation."""
        code = """
def complex_function(x):
    if x > 0:
        if x > 10:
            for i in range(x):
                if i % 2 == 0:
                    print(i)
        else:
            while x > 0:
                x -= 1
    else:
        try:
            raise ValueError("Negative value")
        except ValueError:
            return -1
    return x
"""
        
        analyzer = PythonASTAnalyzer()
        result = analyzer.calculate_complexity_metrics(code)
        
        assert result["success"] is True
        assert result["cyclomatic_complexity"] > 1  # Should be complex
        assert result["nesting_depth"] > 1  # Should have nested structures
        assert result["total_lines"] > 10
        assert result["function_count"] == 1
    
    def test_extract_dependencies(self):
        """Test dependency extraction."""
        code = """
import os
import sys
from pathlib import Path
from typing import Dict, List
import json
from collections import defaultdict
"""
        
        analyzer = PythonASTAnalyzer()
        result = analyzer.extract_dependencies(code)
        
        assert result["success"] is True
        assert "os" in result["imports"]
        assert "sys" in result["imports"]
        assert "pathlib" in result["imports"]
        assert "typing" in result["imports"]
        assert "json" in result["imports"]
        assert "collections" in result["imports"]


class TestCodeComplexityMetrics:
    """Test CodeComplexityMetrics class."""
    
    def test_cyclomatic_complexity_simple(self):
        """Test cyclomatic complexity for simple code."""
        code = "def simple(): return 42"
        tree = ast.parse(code)
        
        metrics = CodeComplexityMetrics()
        complexity = metrics.calculate_cyclomatic_complexity(tree)
        
        assert complexity == 1  # Base complexity
    
    def test_cyclomatic_complexity_with_conditions(self):
        """Test cyclomatic complexity with conditions."""
        code = """
def complex_func(x):
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0
"""
        tree = ast.parse(code)
        
        metrics = CodeComplexityMetrics()
        complexity = metrics.calculate_cyclomatic_complexity(tree)
        
        assert complexity > 1  # Should have increased complexity
    
    def test_nesting_depth(self):
        """Test nesting depth calculation."""
        code = """
def nested_func():
    if True:
        if True:
            if True:
                pass
"""
        tree = ast.parse(code)
        
        metrics = CodeComplexityMetrics()
        depth = metrics.calculate_nesting_depth(tree)
        
        assert depth >= 3  # Three levels of nesting


class TestToolFunctions:
    """Test the main tool functions."""
    
    @patch('dev_team.tools.mcp_code_analysis.SerenaAnalyzer')
    def test_analyze_code_with_serena_available(self, mock_serena):
        """Test analyze_code_with_serena when Serena is available."""
        mock_instance = Mock()
        mock_instance.is_available = True
        mock_instance.analyze_code.return_value = {
            "success": True,
            "symbols": [{"name": "test", "type": "function"}],
            "diagnostics": []
        }
        mock_serena.return_value = mock_instance
        
        result = analyze_code_with_serena("def test(): pass", "test.py")
        
        assert result["success"] is True
        assert len(result["symbols"]) == 1
    
    @patch('dev_team.tools.mcp_code_analysis.RepoMapperAnalyzer')
    def test_analyze_repository_structure_tool(self, mock_analyzer):
        """Test analyze_repository_structure tool function."""
        mock_instance = Mock()
        mock_instance.analyze_repository.return_value = {
            "success": True,
            "files": [{"path": "test.py", "type": "python"}],
            "dependencies": {}
        }
        mock_analyzer.return_value = mock_instance
        
        result = analyze_repository_structure("/path/to/repo")
        
        assert result["success"] is True
        assert "files" in result
    
    def test_analyze_python_code_ast_tool(self):
        """Test analyze_python_code_ast tool function."""
        code = "def test_function(): pass"
        
        result = analyze_python_code_ast(code)
        
        assert result["success"] is True
        assert len(result["functions"]) == 1
        assert result["functions"][0]["name"] == "test_function"
    
    def test_find_symbol_definitions_tool(self):
        """Test find_symbol_definitions tool function."""
        code = "def target(): pass"
        
        result = find_symbol_definitions(code, "target")
        
        assert result["success"] is True
        assert len(result["definitions"]) == 1
        assert result["definitions"][0]["name"] == "target"
    
    def test_get_code_complexity_metrics_tool(self):
        """Test get_code_complexity_metrics tool function."""
        code = """
def complex_func(x):
    if x > 0:
        return 1
    else:
        return -1
"""
        
        result = get_code_complexity_metrics(code)
        
        assert result["success"] is True
        assert result["cyclomatic_complexity"] > 1
        assert result["function_count"] == 1
    
    def test_extract_code_dependencies_tool(self):
        """Test extract_code_dependencies tool function."""
        code = "import os\nfrom sys import path"
        
        result = extract_code_dependencies(code)
        
        assert result["success"] is True
        assert "os" in result["imports"]
        assert "sys" in result["imports"]


class TestErrorHandling:
    """Test error handling in MCP code analysis tools."""
    
    def test_analyze_invalid_python_code(self):
        """Test analysis of invalid Python code."""
        invalid_code = "def incomplete_function("
        
        result = analyze_python_code_ast(invalid_code)
        
        assert result["success"] is False
        assert "error" in result
    
    def test_find_symbol_in_invalid_code(self):
        """Test finding symbols in invalid code."""
        invalid_code = "def incomplete("
        
        result = find_symbol_definitions(invalid_code, "test")
        
        assert result["success"] is False
        assert "error" in result
    
    def test_complexity_metrics_invalid_code(self):
        """Test complexity metrics on invalid code."""
        invalid_code = "if without condition:"
        
        result = get_code_complexity_metrics(invalid_code)
        
        assert result["success"] is False
        assert "error" in result


class TestIntegration:
    """Integration tests for MCP code analysis tools."""
    
    def test_real_python_ast_analysis(self):
        """Test real Python AST analysis."""
        code = """
import os
from pathlib import Path

def main():
    '''Main function.'''
    path = Path(".")
    if path.exists():
        print("Path exists")
    
    for file in path.iterdir():
        if file.is_file():
            print(f"File: {file}")

class FileProcessor:
    def __init__(self, base_path):
        self.base_path = base_path
    
    def process(self):
        return len(list(self.base_path.iterdir()))

if __name__ == "__main__":
    main()
"""
        
        # Test AST analysis
        result = analyze_python_code_ast(code)
        assert result["success"] is True
        assert len(result["functions"]) >= 1
        assert len(result["classes"]) >= 1
        
        # Test complexity metrics
        complexity_result = get_code_complexity_metrics(code)
        assert complexity_result["success"] is True
        assert complexity_result["cyclomatic_complexity"] > 1
        
        # Test dependency extraction
        deps_result = extract_code_dependencies(code)
        assert deps_result["success"] is True
        assert "os" in deps_result["imports"]
        assert "pathlib" in deps_result["imports"]
    
    def test_repository_analysis_with_real_files(self):
        """Test repository analysis with real files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a small test repository
            (Path(temp_dir) / "main.py").write_text("""
import utils
from config import settings

def main():
    utils.process_data()
    print(settings.DEBUG)

if __name__ == "__main__":
    main()
""")
            
            (Path(temp_dir) / "utils.py").write_text("""
def process_data():
    return "processed"

def helper_function():
    return True
""")
            
            (Path(temp_dir) / "config.py").write_text("""
class Settings:
    DEBUG = True

settings = Settings()
""")
            
            result = analyze_repository_structure(temp_dir)
            
            assert result["success"] is True
            assert len(result["files"]) == 3
            assert "dependencies" in result


if __name__ == "__main__":
    pytest.main([__file__])
