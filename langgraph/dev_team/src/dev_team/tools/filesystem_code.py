"""Filesystem and code tools."""

import os
import glob
from langchain_core.tools import tool


@tool
def read_file(file_path: str) -> str:
    """Read the contents of a file.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        File contents as string
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"File contents of {file_path}:\n{content}"
    except Exception as e:
        return f"Error reading file {file_path}: {str(e)}"


@tool
def write_file(file_path: str, content: str) -> str:
    """Write content to a file.
    
    Args:
        file_path: Path where to write the file
        content: Content to write
        
    Returns:
        Confirmation of file written
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"File written successfully: {file_path}"
    except Exception as e:
        return f"Error writing file {file_path}: {str(e)}"


@tool
def list_files(directory: str = ".", pattern: str = "*") -> str:
    """List files in a directory with optional pattern matching.
    
    Args:
        directory: Directory to list files from
        pattern: File pattern to match (e.g., "*.py")
        
    Returns:
        List of matching files
    """
    try:
        files = glob.glob(os.path.join(directory, pattern))
        return f"Files in {directory} matching '{pattern}':\n" + "\n".join(files)
    except Exception as e:
        return f"Error listing files: {str(e)}"


__all__ = [
    'read_file',
    'write_file',
    'list_files'
]
