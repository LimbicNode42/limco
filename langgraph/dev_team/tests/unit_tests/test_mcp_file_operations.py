"""Unit tests for MCP File Operations tools."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

from dev_team.tools.mcp_file_operations import (
    FileScopeAnalyzer,
    TextEditor,
    LanguageServerManager,
    FileScope,
    EditOperation,
    LanguageServerInfo,
    analyze_file_importance,
    read_file_efficiently,
    edit_file_at_line,
    edit_file_range,
    get_language_server_info,
    clear_file_cache
)


class TestFileScopeAnalyzer:
    """Test FileScopeAnalyzer class."""
    
    def test_init(self):
        """Test FileScopeAnalyzer initialization."""
        analyzer = FileScopeAnalyzer()
        assert analyzer.supported_extensions is not None
        assert '.py' in analyzer.supported_extensions
        assert '.js' in analyzer.supported_extensions
    
    def test_analyze_project_scope(self):
        """Test project scope analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            (Path(temp_dir) / "main.py").write_text("""
import utils
from config import settings

def main():
    utils.process()
""")
            
            (Path(temp_dir) / "utils.py").write_text("""
def process():
    return "done"

def helper():
    return True
""")
            
            (Path(temp_dir) / "config.py").write_text("""
settings = {"debug": True}
""")
            
            analyzer = FileScopeAnalyzer()
            result = analyzer.analyze_project_scope(temp_dir)
            
            assert len(result) == 3
            for file_path, scope in result.items():
                assert isinstance(scope, FileScope)
                assert scope.file_path == file_path
                assert scope.importance_score >= 0
    
    def test_extract_file_dependencies_python(self):
        """Test Python file dependency extraction."""
        analyzer = FileScopeAnalyzer()
        
        test_file = Path("test.py")
        deps = analyzer._extract_file_dependencies(test_file)
        
        # Should return empty list for non-existent file
        assert isinstance(deps, list)
    
    def test_calculate_importance_score(self):
        """Test importance score calculation."""
        analyzer = FileScopeAnalyzer()
        
        # High importance (many dependents)
        score1 = analyzer._calculate_importance_score(5, 10, 200)
        
        # Low importance (few dependents)
        score2 = analyzer._calculate_importance_score(2, 1, 50)
        
        assert score1 > score2
    
    def test_should_analyze_file(self):
        """Test file analysis filter."""
        analyzer = FileScopeAnalyzer()
        
        # Should analyze regular Python files
        assert analyzer._should_analyze_file(Path("main.py"))
        assert analyzer._should_analyze_file(Path("utils.py"))
        
        # Should skip test files
        assert not analyzer._should_analyze_file(Path("test_main.py"))
        assert not analyzer._should_analyze_file(Path("main_test.py"))
        
        # Should skip files in excluded directories
        assert not analyzer._should_analyze_file(Path("__pycache__/module.py"))
        assert not analyzer._should_analyze_file(Path("node_modules/package.js"))


class TestTextEditor:
    """Test TextEditor class."""
    
    def test_init(self):
        """Test TextEditor initialization."""
        editor = TextEditor()
        assert editor.line_cache == {}
    
    def test_read_file_lines(self):
        """Test reading file lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")
            f.flush()
            
            editor = TextEditor()
            
            # Read all lines
            lines = editor.read_file_lines(f.name)
            assert len(lines) == 5
            assert lines[0] == "Line 1\n"
            
            # Read specific range
            lines = editor.read_file_lines(f.name, 2, 4)
            assert len(lines) == 3
            assert lines[0] == "Line 2\n"
            assert lines[2] == "Line 4\n"
            
            # Clean up
            os.unlink(f.name)
    
    def test_insert_at_line(self):
        """Test inserting content at specific line."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Line 1\nLine 2\nLine 3\n")
            f.flush()
            
            editor = TextEditor()
            
            # Insert at line 2
            result = editor.insert_at_line(f.name, 2, "Inserted Line")
            
            assert result.success is True
            assert result.operation_type == "insert"
            assert result.line_number == 2
            
            # Verify insertion
            with open(f.name, 'r') as read_f:
                content = read_f.read()
                lines = content.split('\n')
                assert "Inserted Line" in lines[1]
            
            # Clean up
            os.unlink(f.name)
    
    def test_replace_lines(self):
        """Test replacing lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Line 1\nLine 2\nLine 3\nLine 4\n")
            f.flush()
            
            editor = TextEditor()
            
            # Replace lines 2-3
            result = editor.replace_lines(f.name, 2, 3, "Replaced Content")
            
            assert result.success is True
            assert result.operation_type == "replace"
            assert result.line_number == 2
            assert result.end_line == 3
            
            # Verify replacement
            with open(f.name, 'r') as read_f:
                content = read_f.read()
                assert "Replaced Content" in content
                assert "Line 2" not in content
                assert "Line 3" not in content
            
            # Clean up
            os.unlink(f.name)
    
    def test_delete_lines(self):
        """Test deleting lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Line 1\nLine 2\nLine 3\nLine 4\n")
            f.flush()
            
            editor = TextEditor()
            
            # Delete line 2
            result = editor.delete_lines(f.name, 2, 2)
            
            assert result.success is True
            assert result.operation_type == "delete"
            
            # Verify deletion
            with open(f.name, 'r') as read_f:
                content = read_f.read()
                assert "Line 2" not in content
                assert "Line 1" in content
                assert "Line 3" in content
            
            # Clean up
            os.unlink(f.name)
    
    def test_clear_cache(self):
        """Test cache clearing."""
        editor = TextEditor()
        
        # Add something to cache
        editor.line_cache["test.txt"] = ["line1", "line2"]
        
        # Clear specific file
        editor.clear_cache("test.txt")
        assert "test.txt" not in editor.line_cache
        
        # Add multiple files
        editor.line_cache["file1.txt"] = ["content1"]
        editor.line_cache["file2.txt"] = ["content2"]
        
        # Clear all
        editor.clear_cache()
        assert len(editor.line_cache) == 0


class TestLanguageServerManager:
    """Test LanguageServerManager class."""
    
    def test_init(self):
        """Test LanguageServerManager initialization."""
        manager = LanguageServerManager()
        assert len(manager.language_servers) > 0
        assert 'python' in manager.language_servers
        assert 'typescript' in manager.language_servers
    
    @patch('subprocess.run')
    def test_check_availability(self, mock_run):
        """Test language server availability checking."""
        # Mock successful server check
        mock_run.return_value = Mock(returncode=0)
        
        manager = LanguageServerManager()
        
        # At least some servers should be marked as available
        # (depending on the mock return value)
        assert isinstance(manager.language_servers['python'].is_available, bool)
    
    def test_get_available_servers(self):
        """Test getting available servers."""
        manager = LanguageServerManager()
        
        # Manually set some servers as available for testing
        manager.language_servers['python'].is_available = True
        manager.language_servers['typescript'].is_available = False
        
        available = manager.get_available_servers()
        
        assert len(available) >= 1
        assert all(server.is_available for server in available)
    
    def test_get_server_for_file(self):
        """Test getting appropriate server for file."""
        manager = LanguageServerManager()
        
        # Set Python server as available
        manager.language_servers['python'].is_available = True
        
        # Test Python file
        server = manager.get_server_for_file("test.py")
        if server:  # Only test if server is available
            assert server.language == 'python'
        
        # Test unknown file extension
        server = manager.get_server_for_file("test.unknown")
        assert server is None


class TestToolFunctions:
    """Test the main tool functions."""
    
    @patch('dev_team.tools.mcp_file_operations.get_file_scope_analyzer')
    def test_analyze_file_importance_tool(self, mock_get_analyzer):
        """Test analyze_file_importance tool function."""
        mock_analyzer = Mock()
        mock_file_scope = Mock()
        mock_file_scope.importance_score = 5.0
        mock_file_scope.dependency_count = 3
        mock_file_scope.file_path = "test.py"
        
        mock_analyzer.analyze_project_scope.return_value = {
            "test.py": mock_file_scope
        }
        mock_get_analyzer.return_value = mock_analyzer
        
        result = analyze_file_importance("/path/to/project")
        
        assert result["success"] is True
        assert "important_files" in result
        assert "summary" in result
    
    def test_read_file_efficiently_tool(self):
        """Test read_file_efficiently tool function."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Line 1\nLine 2\nLine 3\n")
            f.flush()
            
            result = read_file_efficiently(f.name, 1, 2)
            
            assert result["success"] is True
            assert "content" in result
            assert "Line 1" in result["content"]
            assert "Line 2" in result["content"]
            assert "Line 3" not in result["content"]
            
            # Clean up
            os.unlink(f.name)
    
    def test_edit_file_at_line_tool(self):
        """Test edit_file_at_line tool function."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Line 1\nLine 2\nLine 3\n")
            f.flush()
            
            # Test insert operation
            result = edit_file_at_line(f.name, 2, "Inserted Line", "insert")
            
            assert result["success"] is True
            assert result["operation"]["success"] is True
            
            # Verify insertion
            with open(f.name, 'r') as read_f:
                content = read_f.read()
                assert "Inserted Line" in content
            
            # Clean up
            os.unlink(f.name)
    
    def test_edit_file_range_tool(self):
        """Test edit_file_range tool function."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Line 1\nLine 2\nLine 3\nLine 4\n")
            f.flush()
            
            # Test replace operation
            result = edit_file_range(f.name, 2, 3, "Replaced Lines", "replace")
            
            assert result["success"] is True
            assert result["operation"]["success"] is True
            
            # Clean up
            os.unlink(f.name)
    
    @patch('dev_team.tools.mcp_file_operations.get_language_server_manager')
    def test_get_language_server_info_tool(self, mock_get_manager):
        """Test get_language_server_info tool function."""
        mock_manager = Mock()
        mock_server = Mock()
        mock_server.language = 'python'
        mock_server.server_name = 'pylsp'
        
        mock_manager.get_available_servers.return_value = [mock_server]
        mock_get_manager.return_value = mock_manager
        
        result = get_language_server_info()
        
        assert result["success"] is True
        assert "available_servers" in result
    
    def test_clear_file_cache_tool(self):
        """Test clear_file_cache tool function."""
        result = clear_file_cache()
        
        assert result["success"] is True
        assert "message" in result


class TestErrorHandling:
    """Test error handling in file operations tools."""
    
    def test_read_nonexistent_file(self):
        """Test reading non-existent file."""
        result = read_file_efficiently("/nonexistent/file.txt")
        
        assert result["success"] is False
        assert "error" in result
    
    def test_edit_nonexistent_file(self):
        """Test editing non-existent file."""
        result = edit_file_at_line("/nonexistent/file.txt", 1, "content", "insert")
        
        assert result["success"] is False
        assert "error" in result
    
    def test_invalid_edit_operation(self):
        """Test invalid edit operation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("content")
            f.flush()
            
            result = edit_file_at_line(f.name, 1, "content", "invalid_op")
            
            assert result["success"] is False
            assert "Unknown operation" in result["error"]
            
            # Clean up
            os.unlink(f.name)


class TestDataStructures:
    """Test data structure classes."""
    
    def test_file_scope_dataclass(self):
        """Test FileScope dataclass."""
        scope = FileScope(
            file_path="test.py",
            importance_score=5.0,
            dependency_count=3,
            dependents=["main.py"],
            dependencies=["utils.py"],
            file_type="python",
            lines_of_code=100
        )
        
        assert scope.file_path == "test.py"
        assert scope.importance_score == 5.0
        assert scope.dependency_count == 3
        assert len(scope.dependents) == 1
        assert len(scope.dependencies) == 1
    
    def test_edit_operation_dataclass(self):
        """Test EditOperation dataclass."""
        operation = EditOperation(
            operation_type="insert",
            file_path="test.py",
            line_number=5,
            content="new content",
            success=True
        )
        
        assert operation.operation_type == "insert"
        assert operation.file_path == "test.py"
        assert operation.line_number == 5
        assert operation.success is True
    
    def test_language_server_info_dataclass(self):
        """Test LanguageServerInfo dataclass."""
        server_info = LanguageServerInfo(
            language="python",
            server_name="pylsp",
            command=["pylsp"],
            is_available=True
        )
        
        assert server_info.language == "python"
        assert server_info.server_name == "pylsp"
        assert server_info.is_available is True


class TestIntegration:
    """Integration tests for file operations tools."""
    
    def test_real_file_operations(self):
        """Test real file operations end-to-end."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("""
def original_function():
    return "original"

class OriginalClass:
    pass
""")
            
            # Read file
            read_result = read_file_efficiently(str(test_file))
            assert read_result["success"] is True
            assert "original_function" in read_result["content"]
            
            # Edit file - insert new function
            edit_result = edit_file_at_line(
                str(test_file), 
                2, 
                "def new_function():\n    return 'new'\n", 
                "insert"
            )
            assert edit_result["success"] is True
            
            # Read again to verify
            read_result2 = read_file_efficiently(str(test_file))
            assert read_result2["success"] is True
            assert "new_function" in read_result2["content"]
    
    def test_project_analysis_integration(self):
        """Test project analysis integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a small project
            (Path(temp_dir) / "main.py").write_text("""
import utils
from config import settings

def main():
    utils.process()
    print(settings.DEBUG)
""")
            
            (Path(temp_dir) / "utils.py").write_text("""
def process():
    return "processed"
""")
            
            (Path(temp_dir) / "config.py").write_text("""
DEBUG = True
""")
            
            # Analyze project
            result = analyze_file_importance(temp_dir)
            
            assert result["success"] is True
            assert result["total_files_analyzed"] >= 3
            assert len(result["important_files"]) >= 1


if __name__ == "__main__":
    pytest.main([__file__])
