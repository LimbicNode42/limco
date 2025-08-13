"""MCP Code Analysis Tools

This module provides code analysis and understanding capabilities using:
- oraios/serena for language server-based symbolic analysis
- pdavis68/RepoMapper for repository structure analysis
- Native AST analysis for Python

Implements hybrid connection strategy:
- Primary: MCP Aggregator connection (MCPX, mcgravity, etc.)
- Secondary: Individual MCP server startup
- Tertiary: Native Python implementations (always available)
"""

import ast
import os
import subprocess
import tempfile
import json
import time
import threading
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
import logging
from dataclasses import dataclass, asdict

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# MCP Server Configuration - Hybrid Approach
# Primary: Connect to MCP Aggregator/Proxy
# Secondary: Start individual MCP servers
MCP_ANALYSIS_CONFIG = {
    "aggregator": {
        "enabled": True,
        "url": os.getenv("MCP_AGGREGATOR_URL", "http://localhost:8080"),
        "timeout": 5,
        "serena_endpoint": "/serena",
        "repo_mapper_endpoint": "/repo-mapper"
    },
    "individual_servers": {
        "serena": {
            "port": int(os.getenv("SERENA_MCP_PORT", "6976")),
            "host": "127.0.0.1",
            "start_command": ["uvx", "--from", "git+https://github.com/oraios/serena", "serena", "start-mcp-server", "--context", "ide-assistant"],
            "health_endpoint": "/health"
        },
        "repo-mapper": {
            "port": int(os.getenv("REPO_MAPPER_MCP_PORT", "6977")),
            "host": "127.0.0.1",
            "start_command": ["repo-mapper-mcp", "--transport", "sse"],
            "health_endpoint": "/health"
        }
    },
    "fallback_native": True,
    "startup_timeout": 30,
    "health_check_interval": 10
}


class MCPAnalysisConnectionManager:
    """Manages hybrid MCP connections for code analysis - aggregator first, individual servers as fallback."""
    
    def __init__(self):
        self.config = MCP_ANALYSIS_CONFIG
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
        """Get connection info for a server type (serena/repo-mapper)."""
        # Try aggregator first
        if self.check_aggregator_health():
            aggregator_config = self.config["aggregator"]
            endpoint = aggregator_config.get(f"{server_type.replace('-', '_')}_endpoint", f"/{server_type}")
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
_mcp_analysis_manager = MCPAnalysisConnectionManager()

# Alias for compatibility with test suite
MCPConnectionManager = MCPAnalysisConnectionManager


@dataclass
class SymbolInfo:
    """Information about a code symbol."""
    name: str
    kind: str  # function, class, variable, method, etc.
    file_path: str
    line_number: int
    column: int
    definition: Optional[str] = None
    docstring: Optional[str] = None
    references: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.references is None:
            self.references = []


@dataclass
class FileAnalysis:
    """Analysis results for a single file."""
    file_path: str
    symbols: List[SymbolInfo]
    imports: List[str]
    dependencies: List[str]
    complexity_score: Optional[int] = None
    lines_of_code: Optional[int] = None
    language: Optional[str] = None


@dataclass
class ProjectStructure:
    """Project structure information."""
    root_path: str
    total_files: int
    languages: Dict[str, int]
    file_tree: Dict[str, Any]
    important_files: List[Dict[str, Any]]
    dependencies: Dict[str, List[str]]


class SerenaAnalyzer:
    """Code analysis using Serena MCP server."""
    
    def __init__(self, serena_command: Optional[List[str]] = None):
        """Initialize Serena analyzer.
        
        Args:
            serena_command: Command to run Serena MCP server
        """
        self.serena_command = serena_command or [
            'uvx', '--from', 'git+https://github.com/oraios/serena',
            'serena', 'start-mcp-server', '--context', 'ide-assistant'
        ]
        self._process = None
        self._available = self._check_serena_availability()
    
    def _check_serena_availability(self) -> bool:
        """Check if Serena is available."""
        try:
            result = subprocess.run(
                ['uvx', '--help'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def is_available(self) -> bool:
        """Check if Serena analyzer is available."""
        return self._available
    
    def analyze_project(self, project_path: str) -> Optional[ProjectStructure]:
        """Analyze project structure using Serena.
        
        Args:
            project_path: Path to project root
            
        Returns:
            ProjectStructure if successful, None otherwise
        """
        if not self.is_available():
            logger.warning("Serena not available, skipping analysis")
            return None
        
        try:
            # This would integrate with Serena's MCP tools
            # For now, we'll return a placeholder
            logger.info(f"Would analyze project with Serena: {project_path}")
            return None
        except Exception as e:
            logger.error(f"Serena analysis failed: {e}")
            return None
    
    def find_symbols(self, query: str, project_path: str) -> List[SymbolInfo]:
        """Find symbols using Serena's semantic search.
        
        Args:
            query: Symbol name or pattern to search for
            project_path: Project root path
            
        Returns:
            List of found symbols
        """
        if not self.is_available():
            return []
        
        try:
            # This would use Serena's find_symbol tool
            logger.info(f"Would search for symbols: {query} in {project_path}")
            return []
        except Exception as e:
            logger.error(f"Symbol search failed: {e}")
            return []


class RepoMapperAnalyzer:
    """Repository analysis using RepoMapper concepts."""
    
    def __init__(self):
        """Initialize RepoMapper analyzer."""
        self._available = True  # We'll implement this natively
    
    def is_available(self) -> bool:
        """Check if RepoMapper analyzer is available."""
        return self._available
    
    def analyze_repository(self, repo_path: str) -> ProjectStructure:
        """Analyze repository structure and dependencies.
        
        Args:
            repo_path: Path to repository root
            
        Returns:
            ProjectStructure with repository analysis
        """
        repo_path = Path(repo_path)
        
        # Count files by language
        languages = {}
        all_files = []
        important_files = []
        
        # Common important file patterns
        important_patterns = [
            'README*', 'LICENSE*', 'CHANGELOG*', 'CONTRIBUTING*',
            'requirements.txt', 'setup.py', 'pyproject.toml', 'Dockerfile',
            'package.json', 'pom.xml', 'Cargo.toml', 'go.mod'
        ]
        
        for file_path in repo_path.rglob('*'):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                all_files.append(str(file_path.relative_to(repo_path)))
                
                # Determine language
                lang = self._get_file_language(file_path)
                if lang:
                    languages[lang] = languages.get(lang, 0) + 1
                
                # Check if it's an important file
                if any(file_path.match(pattern) for pattern in important_patterns):
                    important_files.append({
                        'path': str(file_path.relative_to(repo_path)),
                        'type': 'configuration',
                        'importance': 'high'
                    })
        
        # Build file tree
        file_tree = self._build_file_tree(all_files)
        
        # Analyze dependencies
        dependencies = self._analyze_dependencies(repo_path)
        
        return ProjectStructure(
            root_path=str(repo_path),
            total_files=len(all_files),
            languages=languages,
            file_tree=file_tree,
            important_files=important_files,
            dependencies=dependencies
        )
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored."""
        ignore_patterns = [
            '.*', '__pycache__', 'node_modules', '.git', '.svn',
            'venv', 'env', '.venv', 'build', 'dist', 'target'
        ]
        
        for part in file_path.parts:
            if any(part.startswith(pattern.rstrip('*')) for pattern in ignore_patterns):
                return True
        return False
    
    def _get_file_language(self, file_path: Path) -> Optional[str]:
        """Determine programming language from file extension."""
        ext_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.go': 'Go',
            '.rs': 'Rust',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.clj': 'Clojure',
            '.sql': 'SQL',
            '.sh': 'Shell',
            '.ps1': 'PowerShell',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.json': 'JSON',
            '.xml': 'XML',
            '.html': 'HTML',
            '.css': 'CSS',
            '.md': 'Markdown'
        }
        return ext_map.get(file_path.suffix.lower())
    
    def _build_file_tree(self, files: List[str]) -> Dict[str, Any]:
        """Build hierarchical file tree structure."""
        tree = {}
        
        for file_path in sorted(files):
            parts = file_path.split(os.sep)
            current = tree
            
            for i, part in enumerate(parts):
                if i == len(parts) - 1:  # It's a file
                    current[part] = {'type': 'file', 'path': file_path}
                else:  # It's a directory
                    if part not in current:
                        current[part] = {'type': 'directory', 'children': {}}
                    current = current[part]['children']
        
        return tree
    
    def _analyze_dependencies(self, repo_path: Path) -> Dict[str, List[str]]:
        """Analyze project dependencies."""
        dependencies = {}
        
        # Python dependencies
        for req_file in ['requirements.txt', 'pyproject.toml', 'setup.py']:
            file_path = repo_path / req_file
            if file_path.exists():
                deps = self._parse_python_dependencies(file_path)
                if deps:
                    dependencies['python'] = deps
                break
        
        # Node.js dependencies
        package_json = repo_path / 'package.json'
        if package_json.exists():
            deps = self._parse_node_dependencies(package_json)
            if deps:
                dependencies['nodejs'] = deps
        
        return dependencies
    
    def _parse_python_dependencies(self, file_path: Path) -> List[str]:
        """Parse Python dependencies from various files."""
        try:
            if file_path.name == 'requirements.txt':
                with open(file_path, 'r') as f:
                    return [line.strip().split('==')[0].split('>=')[0].split('<=')[0] 
                           for line in f if line.strip() and not line.startswith('#')]
            
            elif file_path.name == 'pyproject.toml':
                try:
                    import tomllib
                except ImportError:
                    try:
                        import tomli as tomllib
                    except ImportError:
                        return []
                
                with open(file_path, 'rb') as f:
                    data = tomllib.load(f)
                
                deps = []
                if 'project' in data and 'dependencies' in data['project']:
                    deps.extend(data['project']['dependencies'])
                if 'tool' in data and 'poetry' in data['tool'] and 'dependencies' in data['tool']['poetry']:
                    deps.extend(data['tool']['poetry']['dependencies'].keys())
                
                return [dep.split('==')[0].split('>=')[0].split('<=')[0] for dep in deps]
            
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
        
        return []
    
    def _parse_node_dependencies(self, file_path: Path) -> List[str]:
        """Parse Node.js dependencies from package.json."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            deps = []
            for dep_type in ['dependencies', 'devDependencies']:
                if dep_type in data:
                    deps.extend(data[dep_type].keys())
            
            return deps
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return []


class PythonASTAnalyzer:
    """Native Python AST analysis."""
    
    def analyze_file(self, file_path: str) -> FileAnalysis:
        """Analyze Python file using AST.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            FileAnalysis with extracted information
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            symbols = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    symbols.append(SymbolInfo(
                        name=node.name,
                        kind='function',
                        file_path=file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        docstring=ast.get_docstring(node)
                    ))
                
                elif isinstance(node, ast.ClassDef):
                    symbols.append(SymbolInfo(
                        name=node.name,
                        kind='class',
                        file_path=file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        docstring=ast.get_docstring(node)
                    ))
                
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            # Calculate complexity and lines of code
            lines_of_code = len([line for line in content.split('\n') if line.strip()])
            complexity_score = self._calculate_complexity(tree)
            
            return FileAnalysis(
                file_path=file_path,
                symbols=symbols,
                imports=imports,
                dependencies=imports,
                complexity_score=complexity_score,
                lines_of_code=lines_of_code,
                language='Python'
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")
            return FileAnalysis(
                file_path=file_path,
                symbols=[],
                imports=[],
                dependencies=[],
                language='Python'
            )
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity


# Initialize analyzers
_serena_analyzer = None
_repo_mapper_analyzer = None
_python_ast_analyzer = None


def get_serena_analyzer() -> SerenaAnalyzer:
    """Get shared Serena analyzer instance."""
    global _serena_analyzer
    if _serena_analyzer is None:
        _serena_analyzer = SerenaAnalyzer()
    return _serena_analyzer


def get_repo_mapper_analyzer() -> RepoMapperAnalyzer:
    """Get shared RepoMapper analyzer instance."""
    global _repo_mapper_analyzer
    if _repo_mapper_analyzer is None:
        _repo_mapper_analyzer = RepoMapperAnalyzer()
    return _repo_mapper_analyzer


def get_python_ast_analyzer() -> PythonASTAnalyzer:
    """Get shared Python AST analyzer instance."""
    global _python_ast_analyzer
    if _python_ast_analyzer is None:
        _python_ast_analyzer = PythonASTAnalyzer()
    return _python_ast_analyzer


@tool
def analyze_repository_structure(
    repo_path: str,
    use_serena: bool = True
) -> Dict[str, Any]:
    """Analyze repository structure and dependencies using hybrid connection strategy.
    
    Analysis order:
    1. MCP Aggregator (if available and use_serena=True)
    2. Individual MCP servers (serena, repo-mapper)
    3. Native Python implementations (always available)
    
    Args:
        repo_path: Path to repository root
        use_serena: Whether to attempt Serena analysis for enhanced results
        
    Returns:
        Dict with repository analysis results
    """
    try:
        repo_path = os.path.abspath(repo_path)
        analysis_methods = []
        result = {}
        
        # Try MCP-based analysis first if requested
        if use_serena:
            # Try Serena via hybrid connection
            connection_info = _mcp_analysis_manager.get_connection_info("serena")
            
            if connection_info["available"] and connection_info["method"] != "native":
                serena_result = _analyze_via_serena(repo_path, connection_info)
                if serena_result:
                    result["serena_analysis"] = serena_result
                    analysis_methods.append(f"serena_{connection_info['method']}")
                    logger.info(f"Serena analysis completed via {connection_info['method']}")
                else:
                    logger.warning("Serena analysis failed, continuing with native analysis")
            
            # Try RepoMapper via hybrid connection
            connection_info = _mcp_analysis_manager.get_connection_info("repo-mapper")
            
            if connection_info["available"] and connection_info["method"] != "native":
                mapper_result = _analyze_via_repo_mapper(repo_path, connection_info)
                if mapper_result:
                    result["repo_mapper_analysis"] = mapper_result
                    analysis_methods.append(f"repo_mapper_{connection_info['method']}")
                    logger.info(f"RepoMapper analysis completed via {connection_info['method']}")
        
        # Always include native analysis as baseline/fallback
        repo_analyzer = get_repo_mapper_analyzer()
        structure = repo_analyzer.analyze_repository(repo_path)
        result["repository_structure"] = asdict(structure)
        analysis_methods.append("native_repo_mapper")
        
        return {
            "success": True,
            "repository_analysis": result,
            "analysis_methods": analysis_methods,
            "total_files": structure.total_files,
            "languages": structure.languages
        }
        
    except Exception as e:
        logger.error(f"Repository analysis failed: {e}")
        return {
            "success": False,
            "error": f"Analysis failed: {str(e)}",
            "analysis_methods": ["failed"]
        }


def _analyze_via_serena(repo_path: str, connection_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Analyze repository via Serena MCP connection."""
    try:
        if connection_info["method"] == "aggregator":
            response = requests.post(
                f"{connection_info['url']}/analyze_project",
                json={"project_path": repo_path},
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Serena aggregator returned {response.status_code}: {response.text}")
                return None
                
        elif connection_info["method"] == "individual":
            # Individual Serena server analysis
            response = requests.post(
                f"{connection_info['url']}/analyze",
                json={"path": repo_path, "type": "project"},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
    except Exception as e:
        logger.warning(f"Serena MCP analysis failed: {e}")
        return None


def _analyze_via_repo_mapper(repo_path: str, connection_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Analyze repository via RepoMapper MCP connection."""
    try:
        if connection_info["method"] == "aggregator":
            response = requests.post(
                f"{connection_info['url']}/map_repository",
                json={"repo_path": repo_path},
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"RepoMapper aggregator returned {response.status_code}: {response.text}")
                return None
                
        elif connection_info["method"] == "individual":
            # Individual RepoMapper server analysis
            response = requests.post(
                f"{connection_info['url']}/map",
                json={"repository_path": repo_path},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
    except Exception as e:
        logger.warning(f"RepoMapper MCP analysis failed: {e}")
        return None


@tool
def analyze_python_file(
    file_path: str,
    include_ast: bool = True,
    include_symbols: bool = True,
    use_serena: bool = True
) -> Dict[str, Any]:
    """Analyze a Python file for symbols, structure, and complexity using hybrid strategy.
    
    Analysis order:
    1. MCP Aggregator with Serena (if available and use_serena=True)
    2. Individual Serena MCP server
    3. Native Python AST analysis (always available)
    
    Args:
        file_path: Path to Python file
        include_ast: Whether to include AST analysis
        include_symbols: Whether to include symbol extraction
        use_serena: Whether to attempt Serena analysis for enhanced results
        
    Returns:
        Dict with file analysis results
    """
    try:
        file_path = os.path.abspath(file_path)
        
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
        
        if not file_path.endswith('.py'):
            return {
                "success": False,
                "error": f"Not a Python file: {file_path}"
            }
        
        analysis_methods = []
        result = {}
        
        # Try Serena analysis first if requested
        if use_serena:
            connection_info = _mcp_analysis_manager.get_connection_info("serena")
            
            if connection_info["available"] and connection_info["method"] != "native":
                serena_result = _analyze_file_via_serena(file_path, connection_info)
                if serena_result:
                    result["serena_analysis"] = serena_result
                    analysis_methods.append(f"serena_{connection_info['method']}")
                    logger.info(f"Serena file analysis completed via {connection_info['method']}")
        
        # Always include native AST analysis as baseline/fallback
        ast_analyzer = get_python_ast_analyzer()
        file_analysis = ast_analyzer.analyze_file(file_path)
        
        result_dict = asdict(file_analysis)
        result["file_analysis"] = result_dict
        analysis_methods.append("native_ast")
        
        return {
            "success": True,
            "file_path": file_path,
            "analysis_results": result,
            "analysis_methods": analysis_methods,
            "symbols_count": len(file_analysis.symbols),
            "imports_count": len(file_analysis.imports),
            "complexity_score": file_analysis.complexity_score,
            "lines_of_code": file_analysis.lines_of_code
        }
        
    except Exception as e:
        logger.error(f"Python file analysis failed: {e}")
        return {
            "success": False,
            "error": f"Analysis failed: {str(e)}",
            "file_path": file_path,
            "analysis_methods": ["failed"]
        }


def _analyze_file_via_serena(file_path: str, connection_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Analyze Python file via Serena MCP connection."""
    try:
        if connection_info["method"] == "aggregator":
            response = requests.post(
                f"{connection_info['url']}/analyze_file",
                json={"file_path": file_path, "language": "python"},
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Serena aggregator file analysis returned {response.status_code}: {response.text}")
                return None
                
        elif connection_info["method"] == "individual":
            # Individual Serena server file analysis
            response = requests.post(
                f"{connection_info['url']}/analyze",
                json={"path": file_path, "type": "file"},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
    except Exception as e:
        logger.warning(f"Serena file analysis failed: {e}")
        return None


@tool
def find_symbols_in_project(
    project_path: str,
    symbol_name: str,
    symbol_type: Optional[str] = None,
    use_serena: bool = True
) -> Dict[str, Any]:
    """Find symbols across the project using hybrid connection strategy.
    
    Search order:
    1. MCP Aggregator with Serena (if available and use_serena=True)
    2. Individual Serena MCP server
    3. Native Python grep-based search (always available)
    
    Args:
        project_path: Path to project root
        symbol_name: Name of symbol to search for
        symbol_type: Type of symbol (function, class, variable, etc.)
        use_serena: Whether to attempt Serena semantic search
        
    Returns:
        Dict with found symbols and their locations
    """
    try:
        project_path = os.path.abspath(project_path)
        analysis_methods = []
        results = []
        
        # Try Serena semantic search first if requested
        if use_serena:
            connection_info = _mcp_analysis_manager.get_connection_info("serena")
            
            if connection_info["available"] and connection_info["method"] != "native":
                serena_results = _find_symbols_via_serena(project_path, symbol_name, symbol_type, connection_info)
                if serena_results:
                    results.extend(serena_results)
                    analysis_methods.append(f"serena_{connection_info['method']}")
                    logger.info(f"Serena symbol search completed via {connection_info['method']}")
        
        # Always include native search as baseline/fallback
        native_results = _find_symbols_native(project_path, symbol_name, symbol_type)
        if native_results:
            results.extend(native_results)
            analysis_methods.append("native_search")
        
        # Remove duplicates based on file_path and line_number
        unique_results = []
        seen = set()
        for result in results:
            key = (result.get('file_path', ''), result.get('line_number', 0))
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return {
            "success": True,
            "symbol_name": symbol_name,
            "symbol_type": symbol_type,
            "project_path": project_path,
            "results": unique_results,
            "total_found": len(unique_results),
            "analysis_methods": analysis_methods
        }
        
    except Exception as e:
        logger.error(f"Symbol search failed: {e}")
        return {
            "success": False,
            "error": f"Symbol search failed: {str(e)}",
            "symbol_name": symbol_name,
            "analysis_methods": ["failed"]
        }


def _find_symbols_via_serena(project_path: str, symbol_name: str, symbol_type: Optional[str], 
                            connection_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Find symbols via Serena MCP connection."""
    try:
        search_params = {
            "project_path": project_path,
            "symbol_name": symbol_name
        }
        if symbol_type:
            search_params["symbol_type"] = symbol_type
            
        if connection_info["method"] == "aggregator":
            response = requests.post(
                f"{connection_info['url']}/find_symbols",
                json=search_params,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("symbols", [])
            else:
                logger.warning(f"Serena aggregator symbol search returned {response.status_code}: {response.text}")
                return []
                
        elif connection_info["method"] == "individual":
            # Individual Serena server symbol search
            response = requests.post(
                f"{connection_info['url']}/search",
                json=search_params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            else:
                return []
                
    except Exception as e:
        logger.warning(f"Serena symbol search failed: {e}")
        return []


def _find_symbols_native(project_path: str, symbol_name: str, symbol_type: Optional[str]) -> List[Dict[str, Any]]:
    """Find symbols using native Python search."""
    results = []
    
    try:
        # Search for Python files
        for root, dirs, files in os.walk(project_path):
            # Skip common ignore directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', 'env']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            
                        for line_num, line in enumerate(lines, 1):
                            line = line.strip()
                            
                            # Simple pattern matching for symbols
                            if symbol_name in line:
                                # Check for function definitions
                                if symbol_type in [None, 'function'] and f"def {symbol_name}" in line:
                                    results.append({
                                        'file_path': file_path,
                                        'line_number': line_num,
                                        'symbol_type': 'function',
                                        'line_content': line,
                                        'symbol_name': symbol_name
                                    })
                                
                                # Check for class definitions  
                                elif symbol_type in [None, 'class'] and f"class {symbol_name}" in line:
                                    results.append({
                                        'file_path': file_path,
                                        'line_number': line_num,
                                        'symbol_type': 'class',
                                        'line_content': line,
                                        'symbol_name': symbol_name
                                    })
                                
                                # Check for variable assignments
                                elif symbol_type in [None, 'variable'] and f"{symbol_name} =" in line:
                                    results.append({
                                        'file_path': file_path,
                                        'line_number': line_num,
                                        'symbol_type': 'variable',
                                        'line_content': line,
                                        'symbol_name': symbol_name
                                    })
                                
                                # General usage/reference
                                elif symbol_type is None:
                                    results.append({
                                        'file_path': file_path,
                                        'line_number': line_num,
                                        'symbol_type': 'reference',
                                        'line_content': line,
                                        'symbol_name': symbol_name
                                    })
                    
                    except Exception as e:
                        logger.warning(f"Failed to read file {file_path}: {e}")
                        continue
                        
    except Exception as e:
        logger.error(f"Native symbol search failed: {e}")
        
    return results


# Export all tools
__all__ = [
    'SerenaAnalyzer',
    'RepoMapperAnalyzer', 
    'PythonASTAnalyzer',
    'SymbolInfo',
    'FileAnalysis',
    'ProjectStructure',
    'analyze_repository_structure',
    'analyze_python_file',
    'find_symbols_in_project'
]
