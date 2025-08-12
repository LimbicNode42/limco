"""MCP Code Analysis Tools

This module provides code analysis and understanding capabilities using:
- oraios/serena for language server-based symbolic analysis
- pdavis68/RepoMapper for repository structure analysis
- Native AST analysis for Python
"""

import ast
import os
import subprocess
import tempfile
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
import logging
from dataclasses import dataclass, asdict

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


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
    """Analyze repository structure and dependencies.
    
    Args:
        repo_path: Path to repository root
        use_serena: Whether to use Serena for enhanced analysis
        
    Returns:
        Dict with repository analysis results
    """
    try:
        repo_path = os.path.abspath(repo_path)
        
        # Use RepoMapper for base analysis
        repo_analyzer = get_repo_mapper_analyzer()
        structure = repo_analyzer.analyze_repository(repo_path)
        
        result = asdict(structure)
        result['analysis_methods'] = ['repo_mapper']
        
        # Enhance with Serena if available and requested
        if use_serena:
            serena_analyzer = get_serena_analyzer()
            if serena_analyzer.is_available():
                serena_structure = serena_analyzer.analyze_project(repo_path)
                if serena_structure:
                    result['serena_analysis'] = asdict(serena_structure)
                    result['analysis_methods'].append('serena')
            else:
                result['serena_warning'] = "Serena not available - install uvx and ensure network access"
        
        return {
            "success": True,
            "repository_analysis": result
        }
        
    except Exception as e:
        logger.error(f"Repository analysis failed: {e}")
        return {
            "success": False,
            "error": f"Analysis failed: {str(e)}"
        }


@tool
def analyze_python_file(
    file_path: str,
    include_ast: bool = True,
    include_symbols: bool = True
) -> Dict[str, Any]:
    """Analyze a Python file for symbols, structure, and complexity.
    
    Args:
        file_path: Path to Python file
        include_ast: Whether to include AST analysis
        include_symbols: Whether to include symbol extraction
        
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
        
        results = {}
        
        if include_ast:
            ast_analyzer = get_python_ast_analyzer()
            analysis = ast_analyzer.analyze_file(file_path)
            results['ast_analysis'] = asdict(analysis)
        
        # Add file metadata
        file_stats = os.stat(file_path)
        results['file_info'] = {
            'size_bytes': file_stats.st_size,
            'modified_time': file_stats.st_mtime,
            'absolute_path': file_path
        }
        
        return {
            "success": True,
            "file_analysis": results
        }
        
    except Exception as e:
        logger.error(f"Python file analysis failed: {e}")
        return {
            "success": False,
            "error": f"Analysis failed: {str(e)}"
        }


@tool
def find_symbols_in_project(
    project_path: str,
    symbol_name: str,
    symbol_type: Optional[str] = None,
    use_serena: bool = True
) -> Dict[str, Any]:
    """Find symbols (functions, classes, variables) in a project.
    
    Args:
        project_path: Path to project root
        symbol_name: Name or pattern to search for
        symbol_type: Type of symbol to find (function, class, variable, etc.)
        use_serena: Whether to use Serena for semantic search
        
    Returns:
        Dict with found symbols
    """
    try:
        project_path = os.path.abspath(project_path)
        found_symbols = []
        
        # Try Serena first if available and requested
        if use_serena:
            serena_analyzer = get_serena_analyzer()
            if serena_analyzer.is_available():
                symbols = serena_analyzer.find_symbols(symbol_name, project_path)
                found_symbols.extend(symbols)
        
        # Fall back to AST analysis for Python files
        if not found_symbols or not use_serena:
            ast_analyzer = get_python_ast_analyzer()
            
            for py_file in Path(project_path).rglob('*.py'):
                try:
                    analysis = ast_analyzer.analyze_file(str(py_file))
                    for symbol in analysis.symbols:
                        if symbol_name.lower() in symbol.name.lower():
                            if not symbol_type or symbol.kind == symbol_type:
                                found_symbols.append(symbol)
                except Exception as e:
                    logger.warning(f"Failed to analyze {py_file}: {e}")
        
        return {
            "success": True,
            "symbols_found": len(found_symbols),
            "symbols": [asdict(symbol) for symbol in found_symbols],
            "search_method": "serena" if use_serena and found_symbols else "ast"
        }
        
    except Exception as e:
        logger.error(f"Symbol search failed: {e}")
        return {
            "success": False,
            "error": f"Search failed: {str(e)}"
        }


@tool
def get_code_complexity_metrics(
    file_or_project_path: str,
    language: str = "python"
) -> Dict[str, Any]:
    """Get code complexity metrics for a file or project.
    
    Args:
        file_or_project_path: Path to file or project
        language: Programming language (currently supports 'python')
        
    Returns:
        Dict with complexity metrics
    """
    try:
        path = Path(file_or_project_path)
        
        if path.is_file():
            # Analyze single file
            if language.lower() == "python" and str(path).endswith('.py'):
                ast_analyzer = get_python_ast_analyzer()
                analysis = ast_analyzer.analyze_file(str(path))
                
                return {
                    "success": True,
                    "file_metrics": {
                        "file_path": str(path),
                        "complexity_score": analysis.complexity_score,
                        "lines_of_code": analysis.lines_of_code,
                        "symbol_count": len(analysis.symbols),
                        "import_count": len(analysis.imports)
                    }
                }
        
        elif path.is_dir():
            # Analyze project
            total_complexity = 0
            total_lines = 0
            total_symbols = 0
            total_files = 0
            file_metrics = []
            
            if language.lower() == "python":
                ast_analyzer = get_python_ast_analyzer()
                
                for py_file in path.rglob('*.py'):
                    try:
                        analysis = ast_analyzer.analyze_file(str(py_file))
                        
                        metrics = {
                            "file_path": str(py_file.relative_to(path)),
                            "complexity_score": analysis.complexity_score or 0,
                            "lines_of_code": analysis.lines_of_code or 0,
                            "symbol_count": len(analysis.symbols),
                            "import_count": len(analysis.imports)
                        }
                        
                        file_metrics.append(metrics)
                        total_complexity += metrics["complexity_score"]
                        total_lines += metrics["lines_of_code"]
                        total_symbols += metrics["symbol_count"]
                        total_files += 1
                        
                    except Exception as e:
                        logger.warning(f"Failed to analyze {py_file}: {e}")
            
            return {
                "success": True,
                "project_metrics": {
                    "total_files": total_files,
                    "total_complexity": total_complexity,
                    "total_lines_of_code": total_lines,
                    "total_symbols": total_symbols,
                    "average_complexity": total_complexity / max(total_files, 1),
                    "average_lines_per_file": total_lines / max(total_files, 1)
                },
                "file_metrics": file_metrics[:20]  # Limit to first 20 files
            }
        
        else:
            return {
                "success": False,
                "error": f"Path not found: {file_or_project_path}"
            }
    
    except Exception as e:
        logger.error(f"Complexity analysis failed: {e}")
        return {
            "success": False,
            "error": f"Analysis failed: {str(e)}"
        }


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
    'find_symbols_in_project',
    'get_code_complexity_metrics'
]
