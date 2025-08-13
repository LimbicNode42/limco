"""MCP File Operations and Project Management Tools

This module provides file operations and project management capabilities using:
- admica/FileScopeMCP concepts for dependency analysis
- tumf/mcp-text-editor for efficient text editing
- isaacphi/mcp-language-server for language server integration

Implements hybrid connection strategy:
- Primary: MCP Aggregator connection (MCPX, mcgravity, etc.)
- Secondary: Individual MCP server startup
- Tertiary: Native Python implementations (always available)
"""

import os
import re
import json
import subprocess
import tempfile
import time
import threading
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import logging
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# MCP Server Configuration - Hybrid Approach
# Primary: Connect to MCP Aggregator/Proxy
# Secondary: Start individual MCP servers
MCP_FILE_CONFIG = {
    "aggregator": {
        "enabled": True,
        "url": os.getenv("MCP_AGGREGATOR_URL", "http://localhost:8080"),
        "timeout": 5,
        "filescopemcp_endpoint": "/filescopemcp",
        "texteditor_endpoint": "/texteditor",
        "languageserver_endpoint": "/languageserver"
    },
    "individual_servers": {
        "filescopemcp": {
            "port": int(os.getenv("FILESCOPEMCP_PORT", "6971")),
            "host": "127.0.0.1",
            "start_command": ["filescopemcp", "--transport", "sse"],
            "health_endpoint": "/health"
        },
        "texteditor": {
            "port": int(os.getenv("TEXTEDITOR_MCP_PORT", "6972")),
            "host": "127.0.0.1", 
            "start_command": ["mcp-text-editor", "--transport", "sse"],
            "health_endpoint": "/health"
        },
        "languageserver": {
            "port": int(os.getenv("LANGUAGESERVER_MCP_PORT", "6973")),
            "host": "127.0.0.1",
            "start_command": ["mcp-language-server", "--transport", "sse"],
            "health_endpoint": "/health"
        }
    },
    "fallback_native": True,
    "startup_timeout": 30,
    "health_check_interval": 10
}


class MCPFileConnectionManager:
    """Manages hybrid MCP connections for file operations - aggregator first, individual servers as fallback."""
    
    def __init__(self):
        self.config = MCP_FILE_CONFIG
        self.aggregator_available = False
        self.individual_servers = {}
        self.server_processes = {}
        self._lock = threading.Lock()
        
    def check_aggregator_health(self) -> bool:
        """Check if MCP aggregator is available."""
        if not self.config["aggregator"]["enabled"]:
            return False
            
        try:
            url = self.config["aggregator"]["url"]
            timeout = self.config["aggregator"]["timeout"]
            response = requests.get(f"{url}/health", timeout=timeout)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Aggregator health check failed: {e}")
            return False
    
    def start_individual_server(self, server_name: str) -> bool:
        """Start an individual MCP server."""
        if server_name in self.server_processes:
            return True  # Already running
            
        config = self.config["individual_servers"].get(server_name)
        if not config:
            logger.error(f"No configuration found for server: {server_name}")
            return False
        
        # Check if command exists
        cmd_name = config["start_command"][0]
        if not self._check_command_exists(cmd_name):
            logger.warning(f"Command '{cmd_name}' not found, cannot start {server_name} server")
            return False
            
        try:
            # Build command with host and port
            cmd = config["start_command"] + [
                "--host", config["host"],
                "--port", str(config["port"])
            ]
            
            logger.info(f"Starting {server_name} MCP server: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Store process reference
            with self._lock:
                self.server_processes[server_name] = process
            
            # Wait a bit for server to start
            time.sleep(2)
            
            # Check if server is healthy
            if self.check_individual_server_health(server_name):
                logger.info(f"{server_name} MCP server started successfully")
                return True
            else:
                logger.error(f"{server_name} MCP server failed health check")
                self.stop_individual_server(server_name)
                return False
                
        except Exception as e:
            logger.error(f"Failed to start {server_name} MCP server: {e}")
            return False
    
    def _check_command_exists(self, command: str) -> bool:
        """Check if a command exists in the system PATH."""
        try:
            subprocess.run([command, "--version"], capture_output=True, timeout=5)
            return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def check_individual_server_health(self, server_name: str) -> bool:
        """Check health of individual MCP server."""
        config = self.config["individual_servers"].get(server_name)
        if not config:
            return False
            
        try:
            url = f"http://{config['host']}:{config['port']}{config['health_endpoint']}"
            response = requests.get(url, timeout=2)
            return response.status_code == 200
        except Exception:
            return False
    
    def stop_individual_server(self, server_name: str):
        """Stop an individual MCP server."""
        with self._lock:
            if server_name in self.server_processes:
                process = self.server_processes[server_name]
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                except Exception as e:
                    logger.warning(f"Error stopping {server_name} server: {e}")
                finally:
                    del self.server_processes[server_name]
    
    def get_connection_info(self, server_type: str) -> Dict[str, Any]:
        """Get connection info for a server type (filescopemcp/texteditor/languageserver)."""
        # Try aggregator first
        if self.check_aggregator_health():
            aggregator_config = self.config["aggregator"]
            endpoint = aggregator_config.get(f"{server_type}_endpoint", f"/{server_type}")
            return {
                "method": "aggregator",
                "url": f"{aggregator_config['url']}{endpoint}",
                "available": True
            }
        
        # Try individual server
        with self._lock:
            if not self.check_individual_server_health(server_type):
                if self.start_individual_server(server_type):
                    config = self.config["individual_servers"][server_type]
                    return {
                        "method": "individual",
                        "url": f"http://{config['host']}:{config['port']}",
                        "available": True
                    }
            else:
                config = self.config["individual_servers"][server_type]
                return {
                    "method": "individual",
                    "url": f"http://{config['host']}:{config['port']}",
                    "available": True
                }
        
        # Fallback to native - always available
        return {
            "method": "native",
            "url": None,
            "available": True  # Native implementations should always be available
        }
    
    def cleanup(self):
        """Clean up all running servers."""
        for server_name in list(self.server_processes.keys()):
            self.stop_individual_server(server_name)


# Global connection manager instance
_mcp_file_manager = MCPFileConnectionManager()

# Alias for compatibility with test suite
MCPConnectionManager = MCPFileConnectionManager


@dataclass
class FileScope:
    """File scope and importance information."""
    file_path: str
    importance_score: float
    dependency_count: int
    dependents: List[str]
    dependencies: List[str]
    file_type: str
    lines_of_code: int


@dataclass
class EditOperation:
    """Text editing operation."""
    operation_type: str  # insert, delete, replace
    file_path: str
    line_number: int
    content: Optional[str] = None
    end_line: Optional[int] = None
    success: bool = False
    error: Optional[str] = None


@dataclass
class LanguageServerInfo:
    """Language server information."""
    language: str
    server_name: str
    command: List[str]
    is_available: bool
    initialization_options: Optional[Dict[str, Any]] = None


class FileScopeAnalyzer:
    """File scope and importance analysis inspired by admica/FileScopeMCP."""
    
    def __init__(self):
        """Initialize FileScopeAnalyzer."""
        self.supported_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby'
        }
    
    def analyze_project_scope(self, project_path: str) -> Dict[str, FileScope]:
        """Analyze file scope and importance in a project.
        
        Args:
            project_path: Path to project root
            
        Returns:
            Dict mapping file paths to FileScope objects
        """
        project_path = Path(project_path)
        file_scopes = {}
        
        # Find all source files
        source_files = []
        for ext in self.supported_extensions:
            source_files.extend(project_path.rglob(f'*{ext}'))
        
        # Analyze dependencies between files
        dependency_graph = self._build_dependency_graph(source_files)
        
        # Calculate importance scores
        for file_path in source_files:
            if self._should_analyze_file(file_path):
                scope = self._analyze_single_file(file_path, dependency_graph)
                file_scopes[str(file_path)] = scope
        
        return file_scopes
    
    def _build_dependency_graph(self, files: List[Path]) -> Dict[str, Dict[str, List[str]]]:
        """Build dependency graph between files."""
        graph = {
            'dependencies': {},  # file -> files it depends on
            'dependents': {}     # file -> files that depend on it
        }
        
        for file_path in files:
            file_str = str(file_path)
            graph['dependencies'][file_str] = []
            graph['dependents'][file_str] = []
        
        # Analyze imports/includes for each file
        for file_path in files:
            try:
                deps = self._extract_file_dependencies(file_path)
                file_str = str(file_path)
                
                for dep in deps:
                    # Try to resolve dependency to actual file
                    resolved_dep = self._resolve_dependency(file_path, dep)
                    if resolved_dep and resolved_dep in graph['dependencies']:
                        graph['dependencies'][file_str].append(resolved_dep)
                        graph['dependents'][resolved_dep].append(file_str)
                        
            except Exception as e:
                logger.warning(f"Failed to analyze dependencies for {file_path}: {e}")
        
        return graph
    
    def _extract_file_dependencies(self, file_path: Path) -> List[str]:
        """Extract dependencies from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            dependencies = []
            ext = file_path.suffix.lower()
            
            if ext == '.py':
                # Python imports
                import_patterns = [
                    r'^\s*import\s+(\w+(?:\.\w+)*)',
                    r'^\s*from\s+(\w+(?:\.\w+)*)\s+import',
                ]
                for pattern in import_patterns:
                    matches = re.findall(pattern, content, re.MULTILINE)
                    dependencies.extend(matches)
            
            elif ext in ['.js', '.ts']:
                # JavaScript/TypeScript imports
                import_patterns = [
                    r'import.*from\s+["\']([^"\']+)["\']',
                    r'require\s*\(\s*["\']([^"\']+)["\']\s*\)',
                ]
                for pattern in import_patterns:
                    matches = re.findall(pattern, content)
                    dependencies.extend(matches)
            
            elif ext == '.java':
                # Java imports
                pattern = r'^\s*import\s+([\w.]+);'
                matches = re.findall(pattern, content, re.MULTILINE)
                dependencies.extend(matches)
            
            elif ext in ['.cpp', '.c']:
                # C/C++ includes
                pattern = r'^\s*#include\s*[<"]([^>"]+)[>"]'
                matches = re.findall(pattern, content, re.MULTILINE)
                dependencies.extend(matches)
            
            return dependencies
            
        except Exception as e:
            logger.warning(f"Failed to extract dependencies from {file_path}: {e}")
            return []
    
    def _resolve_dependency(self, source_file: Path, dependency: str) -> Optional[str]:
        """Resolve a dependency string to an actual file path."""
        try:
            project_root = self._find_project_root(source_file)
            
            # Try different resolution strategies
            candidates = []
            
            # For relative imports
            if dependency.startswith('.'):
                rel_path = source_file.parent / (dependency.replace('.', '/') + '.py')
                candidates.append(rel_path)
            
            # For absolute imports in Python
            elif '.' in dependency:
                module_path = project_root / dependency.replace('.', '/')
                candidates.extend([
                    module_path.with_suffix('.py'),
                    module_path / '__init__.py'
                ])
            
            # For single module names
            else:
                candidates.extend([
                    project_root / f"{dependency}.py",
                    project_root / dependency / '__init__.py'
                ])
            
            # Return first existing candidate
            for candidate in candidates:
                if candidate.exists():
                    return str(candidate)
            
            return None
            
        except Exception:
            return None
    
    def _find_project_root(self, file_path: Path) -> Path:
        """Find project root directory."""
        current = file_path.parent
        
        # Look for common project markers
        markers = [
            '.git', '.hg', '.svn',
            'pyproject.toml', 'setup.py', 'requirements.txt',
            'package.json', 'pom.xml', 'Cargo.toml'
        ]
        
        while current != current.parent:
            if any((current / marker).exists() for marker in markers):
                return current
            current = current.parent
        
        return file_path.parent
    
    def _analyze_single_file(self, file_path: Path, dependency_graph: Dict) -> FileScope:
        """Analyze a single file for scope information."""
        file_str = str(file_path)
        
        # Count lines of code
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            lines_of_code = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        except:
            lines_of_code = 0
        
        # Get dependencies and dependents
        dependencies = dependency_graph['dependencies'].get(file_str, [])
        dependents = dependency_graph['dependents'].get(file_str, [])
        
        # Calculate importance score
        importance_score = self._calculate_importance_score(
            len(dependencies), len(dependents), lines_of_code
        )
        
        return FileScope(
            file_path=file_str,
            importance_score=importance_score,
            dependency_count=len(dependencies),
            dependents=dependents,
            dependencies=dependencies,
            file_type=self.supported_extensions.get(file_path.suffix.lower(), 'unknown'),
            lines_of_code=lines_of_code
        )
    
    def _calculate_importance_score(self, dep_count: int, dependent_count: int, loc: int) -> float:
        """Calculate file importance score."""
        # Files with more dependents are more important
        dependent_score = dependent_count * 2.0
        
        # Files with moderate dependencies are often central
        if dep_count > 0:
            dependency_score = min(dep_count * 0.5, 5.0)  # Cap at 5
        else:
            dependency_score = 0
        
        # Larger files might be more important, but with diminishing returns
        size_score = min(loc / 100.0, 3.0)  # Cap at 3
        
        return dependent_score + dependency_score + size_score
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """Check if file should be analyzed."""
        # Skip test files, generated files, etc.
        skip_patterns = ['test_', '_test.', '.test.', 'spec.', '.spec.']
        skip_dirs = ['__pycache__', 'node_modules', '.git', 'build', 'dist']
        
        file_name = file_path.name.lower()
        if any(pattern in file_name for pattern in skip_patterns):
            return False
        
        for part in file_path.parts:
            if part in skip_dirs:
                return False
        
        return True


class TextEditor:
    """Efficient text editing inspired by tumf/mcp-text-editor."""
    
    def __init__(self):
        """Initialize TextEditor."""
        self.line_cache = {}  # Cache file contents for efficiency
    
    def read_file_lines(self, file_path: str, start_line: int = 1, end_line: Optional[int] = None) -> List[str]:
        """Read specific lines from a file.
        
        Args:
            file_path: Path to file
            start_line: Starting line number (1-based)
            end_line: Ending line number (1-based), None for end of file
            
        Returns:
            List of lines
        """
        try:
            if file_path not in self.line_cache:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.line_cache[file_path] = f.readlines()
            
            lines = self.line_cache[file_path]
            start_idx = max(0, start_line - 1)
            end_idx = len(lines) if end_line is None else min(len(lines), end_line)
            
            return lines[start_idx:end_idx]
            
        except Exception as e:
            logger.error(f"Failed to read lines from {file_path}: {e}")
            return []
    
    def insert_at_line(self, file_path: str, line_number: int, content: str) -> EditOperation:
        """Insert content at a specific line.
        
        Args:
            file_path: Path to file
            line_number: Line number to insert at (1-based)
            content: Content to insert
            
        Returns:
            EditOperation with result
        """
        try:
            # Read current file content
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Insert content
            insert_idx = max(0, min(line_number - 1, len(lines)))
            if not content.endswith('\n'):
                content += '\n'
            
            lines.insert(insert_idx, content)
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            # Update cache
            self.line_cache[file_path] = lines
            
            return EditOperation(
                operation_type='insert',
                file_path=file_path,
                line_number=line_number,
                content=content,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Failed to insert at line {line_number} in {file_path}: {e}")
            return EditOperation(
                operation_type='insert',
                file_path=file_path,
                line_number=line_number,
                content=content,
                success=False,
                error=str(e)
            )
    
    def replace_lines(self, file_path: str, start_line: int, end_line: int, content: str) -> EditOperation:
        """Replace a range of lines with new content.
        
        Args:
            file_path: Path to file
            start_line: Starting line number (1-based)
            end_line: Ending line number (1-based)
            content: New content
            
        Returns:
            EditOperation with result
        """
        try:
            # Read current file content
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Replace lines
            start_idx = max(0, start_line - 1)
            end_idx = min(len(lines), end_line)
            
            if not content.endswith('\n') and content:
                content += '\n'
            
            new_lines = lines[:start_idx] + [content] + lines[end_idx:]
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            # Update cache
            self.line_cache[file_path] = new_lines
            
            return EditOperation(
                operation_type='replace',
                file_path=file_path,
                line_number=start_line,
                end_line=end_line,
                content=content,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Failed to replace lines {start_line}-{end_line} in {file_path}: {e}")
            return EditOperation(
                operation_type='replace',
                file_path=file_path,
                line_number=start_line,
                end_line=end_line,
                content=content,
                success=False,
                error=str(e)
            )
    
    def delete_lines(self, file_path: str, start_line: int, end_line: int) -> EditOperation:
        """Delete a range of lines.
        
        Args:
            file_path: Path to file
            start_line: Starting line number (1-based)
            end_line: Ending line number (1-based)
            
        Returns:
            EditOperation with result
        """
        try:
            # Read current file content
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Delete lines
            start_idx = max(0, start_line - 1)
            end_idx = min(len(lines), end_line)
            
            new_lines = lines[:start_idx] + lines[end_idx:]
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            # Update cache
            self.line_cache[file_path] = new_lines
            
            return EditOperation(
                operation_type='delete',
                file_path=file_path,
                line_number=start_line,
                end_line=end_line,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Failed to delete lines {start_line}-{end_line} in {file_path}: {e}")
            return EditOperation(
                operation_type='delete',
                file_path=file_path,
                line_number=start_line,
                end_line=end_line,
                success=False,
                error=str(e)
            )
    
    def clear_cache(self, file_path: Optional[str] = None):
        """Clear line cache for a file or all files."""
        if file_path:
            self.line_cache.pop(file_path, None)
        else:
            self.line_cache.clear()


class LanguageServerManager:
    """Language server management inspired by isaacphi/mcp-language-server."""
    
    def __init__(self):
        """Initialize LanguageServerManager."""
        self.language_servers = {
            'python': LanguageServerInfo(
                language='python',
                server_name='pylsp',
                command=['pylsp'],
                is_available=False
            ),
            'typescript': LanguageServerInfo(
                language='typescript',
                server_name='typescript-language-server',
                command=['typescript-language-server', '--stdio'],
                is_available=False
            ),
            'javascript': LanguageServerInfo(
                language='javascript',
                server_name='typescript-language-server',
                command=['typescript-language-server', '--stdio'],
                is_available=False
            ),
            'go': LanguageServerInfo(
                language='go',
                server_name='gopls',
                command=['gopls'],
                is_available=False
            ),
            'rust': LanguageServerInfo(
                language='rust',
                server_name='rust-analyzer',
                command=['rust-analyzer'],
                is_available=False
            )
        }
        self._check_availability()
    
    def _check_availability(self):
        """Check which language servers are available."""
        for lang, server_info in self.language_servers.items():
            try:
                result = subprocess.run(
                    server_info.command + ['--help'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                server_info.is_available = result.returncode == 0
            except:
                server_info.is_available = False
    
    def get_available_servers(self) -> List[LanguageServerInfo]:
        """Get list of available language servers."""
        return [server for server in self.language_servers.values() if server.is_available]
    
    def get_server_for_file(self, file_path: str) -> Optional[LanguageServerInfo]:
        """Get appropriate language server for a file."""
        ext = Path(file_path).suffix.lower()
        
        lang_map = {
            '.py': 'python',
            '.ts': 'typescript',
            '.js': 'javascript',
            '.go': 'go',
            '.rs': 'rust'
        }
        
        language = lang_map.get(ext)
        if language and language in self.language_servers:
            server = self.language_servers[language]
            return server if server.is_available else None
        
        return None


# Initialize managers
_file_scope_analyzer = None
_text_editor = None
_language_server_manager = None


def get_file_scope_analyzer() -> FileScopeAnalyzer:
    """Get shared FileScopeAnalyzer instance."""
    global _file_scope_analyzer
    if _file_scope_analyzer is None:
        _file_scope_analyzer = FileScopeAnalyzer()
    return _file_scope_analyzer


def get_text_editor() -> TextEditor:
    """Get shared TextEditor instance."""
    global _text_editor
    if _text_editor is None:
        _text_editor = TextEditor()
    return _text_editor


def get_language_server_manager() -> LanguageServerManager:
    """Get shared LanguageServerManager instance."""
    global _language_server_manager
    if _language_server_manager is None:
        _language_server_manager = LanguageServerManager()
    return _language_server_manager


@tool
def analyze_file_importance(
    project_path: str,
    max_files: int = 50
) -> Dict[str, Any]:
    """Analyze file importance and dependencies in a project using hybrid MCP connection.
    
    Args:
        project_path: Path to project root
        max_files: Maximum number of files to analyze
        
    Returns:
        Dict with file importance analysis
    """
    try:
        connection_info = _mcp_file_manager.get_connection_info("filescopemcp")
        
        if connection_info["method"] in ["aggregator", "individual"]:
            # Use MCP server
            payload = {
                "method": "tools/call",
                "params": {
                    "name": "analyze_file_importance",
                    "arguments": {
                        "project_path": project_path,
                        "max_files": max_files
                    }
                }
            }
            
            try:
                response = requests.post(
                    f"{connection_info['url']}/mcp",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    result["connection_method"] = connection_info["method"]
                    return result
                else:
                    logger.warning(f"MCP server returned {response.status_code}, falling back to native")
            except Exception as e:
                logger.warning(f"MCP connection failed: {e}, falling back to native")
        
        # Native fallback implementation
        logger.info("Using native file importance analysis")
        analyzer = get_file_scope_analyzer()
        file_scopes = analyzer.analyze_project_scope(project_path)
        
        # Sort by importance score
        sorted_files = sorted(
            file_scopes.values(),
            key=lambda x: x.importance_score,
            reverse=True
        )
        
        # Limit results
        top_files = sorted_files[:max_files]
        
        return {
            "success": True,
            "connection_method": "native",
            "total_files_analyzed": len(file_scopes),
            "important_files": [asdict(file_scope) for file_scope in top_files],
            "summary": {
                "highest_importance": top_files[0].importance_score if top_files else 0,
                "average_importance": sum(f.importance_score for f in sorted_files) / len(sorted_files) if sorted_files else 0,
                "total_dependencies": sum(f.dependency_count for f in sorted_files)
            }
        }
        
    except Exception as e:
        logger.error(f"File importance analysis failed: {e}")
        return {
            "success": False,
            "error": f"Analysis failed: {str(e)}",
            "connection_method": "native"
        }


@tool
def read_file_efficiently(
    file_path: str,
    start_line: int = 1,
    end_line: Optional[int] = None,
    max_lines: int = 1000
) -> Dict[str, Any]:
    """Read file content efficiently with line-based access.
    
    Args:
        file_path: Path to file
        start_line: Starting line number (1-based)
        end_line: Ending line number (1-based), None for end of file
        max_lines: Maximum number of lines to read
        
    Returns:
        Dict with file content and metadata
    """
    try:
        editor = get_text_editor()
        
        # Limit the number of lines to prevent excessive output
        if end_line is None:
            # Read a reasonable chunk
            end_line = start_line + max_lines - 1
        elif end_line - start_line + 1 > max_lines:
            end_line = start_line + max_lines - 1
        
        lines = editor.read_file_lines(file_path, start_line, end_line)
        
        # Get file info
        file_stats = os.stat(file_path)
        
        return {
            "success": True,
            "file_path": file_path,
            "start_line": start_line,
            "end_line": end_line,
            "lines_read": len(lines),
            "content": ''.join(lines),
            "file_info": {
                "size_bytes": file_stats.st_size,
                "modified_time": file_stats.st_mtime,
                "total_lines": len(editor.read_file_lines(file_path)) if file_path not in editor.line_cache else len(editor.line_cache[file_path])
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        return {
            "success": False,
            "error": f"Failed to read file: {str(e)}"
        }


@tool
def edit_file_at_line(
    file_path: str,
    line_number: int,
    content: str,
    operation: str = "insert"
) -> Dict[str, Any]:
    """Edit file at a specific line using efficient line-based operations.
    
    Args:
        file_path: Path to file
        line_number: Line number for operation (1-based)
        content: Content to insert or replace with
        operation: Type of operation ('insert', 'replace', 'delete')
        
    Returns:
        Dict with operation result
    """
    try:
        editor = get_text_editor()
        
        if operation == "insert":
            result = editor.insert_at_line(file_path, line_number, content)
        elif operation == "replace":
            # For replace, we replace just the single line
            result = editor.replace_lines(file_path, line_number, line_number, content)
        elif operation == "delete":
            result = editor.delete_lines(file_path, line_number, line_number)
        else:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}. Use 'insert', 'replace', or 'delete'"
            }
        
        return {
            "success": result.success,
            "operation": asdict(result),
            "error": result.error
        }
        
    except Exception as e:
        logger.error(f"File edit operation failed: {e}")
        return {
            "success": False,
            "error": f"Edit operation failed: {str(e)}"
        }


@tool
def edit_file_range(
    file_path: str,
    start_line: int,
    end_line: int,
    content: str,
    operation: str = "replace"
) -> Dict[str, Any]:
    """Edit a range of lines in a file.
    
    Args:
        file_path: Path to file
        start_line: Starting line number (1-based)
        end_line: Ending line number (1-based)
        content: Content to replace with (for replace operation)
        operation: Type of operation ('replace' or 'delete')
        
    Returns:
        Dict with operation result
    """
    try:
        editor = get_text_editor()
        
        if operation == "replace":
            result = editor.replace_lines(file_path, start_line, end_line, content)
        elif operation == "delete":
            result = editor.delete_lines(file_path, start_line, end_line)
        else:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}. Use 'replace' or 'delete'"
            }
        
        return {
            "success": result.success,
            "operation": asdict(result),
            "error": result.error
        }
        
    except Exception as e:
        logger.error(f"File range edit operation failed: {e}")
        return {
            "success": False,
            "error": f"Edit operation failed: {str(e)}"
        }


@tool
def get_language_server_info(
    file_path: Optional[str] = None
) -> Dict[str, Any]:
    """Get information about available language servers.
    
    Args:
        file_path: Optional file path to get specific server info
        
    Returns:
        Dict with language server information
    """
    try:
        manager = get_language_server_manager()
        
        if file_path:
            server = manager.get_server_for_file(file_path)
            if server:
                return {
                    "success": True,
                    "file_path": file_path,
                    "language_server": asdict(server)
                }
            else:
                return {
                    "success": False,
                    "error": f"No language server available for {file_path}"
                }
        else:
            available_servers = manager.get_available_servers()
            return {
                "success": True,
                "available_servers": [asdict(server) for server in available_servers],
                "total_available": len(available_servers)
            }
        
    except Exception as e:
        logger.error(f"Language server info retrieval failed: {e}")
        return {
            "success": False,
            "error": f"Failed to get language server info: {str(e)}"
        }


@tool
def clear_file_cache(
    file_path: Optional[str] = None
) -> Dict[str, Any]:
    """Clear file content cache to free memory or reload files.
    
    Args:
        file_path: Optional specific file to clear from cache
        
    Returns:
        Dict with cache clear result
    """
    try:
        editor = get_text_editor()
        editor.clear_cache(file_path)
        
        return {
            "success": True,
            "message": f"Cache cleared for {file_path if file_path else 'all files'}"
        }
        
    except Exception as e:
        logger.error(f"Cache clear failed: {e}")
        return {
            "success": False,
            "error": f"Failed to clear cache: {str(e)}"
        }


# Export all tools
__all__ = [
    'FileScopeAnalyzer',
    'TextEditor',
    'LanguageServerManager',
    'FileScope',
    'EditOperation',
    'LanguageServerInfo',
    'analyze_file_importance',
    'read_file_efficiently',
    'edit_file_at_line',
    'edit_file_range',
    'get_language_server_info',
    'clear_file_cache'
]
