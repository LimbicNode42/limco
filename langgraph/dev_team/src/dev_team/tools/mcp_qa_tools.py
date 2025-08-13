"""MCP QA and Testing Tools

This module provides QA and testing capabilities using:
- hyperb1iss/lucidity-mcp for code quality analysis
- qainsights/locust-mcp-server for load/performance testing
"""

import os
import re
import json
import ast
import subprocess
import tempfile
import time
import threading
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import logging
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# MCP Server Configuration - Hybrid Approach
# Primary: Connect to MCP Aggregator/Proxy
# Secondary: Start individual MCP servers
MCP_CONFIG = {
    "aggregator": {
        "enabled": True,
        "url": os.getenv("MCP_AGGREGATOR_URL", "http://localhost:8080"),
        "timeout": 5,
        "lucidity_endpoint": "/lucidity",
        "locust_endpoint": "/locust"
    },
    "individual_servers": {
        "lucidity": {
            "port": int(os.getenv("LUCIDITY_MCP_PORT", "6969")),
            "host": "127.0.0.1",
            "start_command": ["lucidity-mcp", "--transport", "sse"],
            "health_endpoint": "/sse"  # Lucidity uses SSE endpoint
        },
        "locust": {
            "port": int(os.getenv("LOCUST_MCP_PORT", "6970")),
            "host": "127.0.0.1", 
            "start_command": ["locust-mcp", "--transport", "sse"],
            "health_endpoint": "/health"
        }
    },
    "fallback_native": True,
    "startup_timeout": 30,
    "health_check_interval": 10
}


class MCPConnectionManager:
    """Manages hybrid MCP connections - aggregator first, individual servers as fallback."""
    
    def __init__(self):
        self.config = MCP_CONFIG
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
            
            self.server_processes[server_name] = process
            
            # Wait for server to start
            max_wait = self.config["startup_timeout"]
            wait_time = 0
            
            while wait_time < max_wait:
                if self.check_individual_server_health(server_name):
                    logger.info(f"{server_name} MCP server started successfully")
                    return True
                time.sleep(1)
                wait_time += 1
                
            logger.error(f"Failed to start {server_name} MCP server within {max_wait}s")
            self.stop_individual_server(server_name)
            return False
            
        except Exception as e:
            logger.error(f"Failed to start {server_name} MCP server: {e}")
            return False
    
    def _check_command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH."""
        try:
            subprocess.run([command, "--version"], 
                         capture_output=True, 
                         timeout=5)
            return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def check_individual_server_health(self, server_name: str) -> bool:
        """Check if individual MCP server is healthy."""
        config = self.config["individual_servers"].get(server_name)
        if not config:
            return False
            
        try:
            url = f"http://{config['host']}:{config['port']}{config['health_endpoint']}"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def stop_individual_server(self, server_name: str):
        """Stop an individual MCP server."""
        if server_name in self.server_processes:
            try:
                process = self.server_processes[server_name]
                process.terminate()
                process.wait(timeout=10)
            except Exception as e:
                logger.warning(f"Error stopping {server_name} server: {e}")
            finally:
                del self.server_processes[server_name]
    
    def get_connection_info(self, server_type: str) -> Dict[str, Any]:
        """Get connection info for a server type (lucidity/locust)."""
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
_mcp_manager = MCPConnectionManager()


@dataclass
class CodeQualityIssue:
    """Code quality issue detected by analysis."""
    dimension: str
    severity: str
    file_path: str
    line_number: Optional[int]
    description: str
    recommendation: str
    code_snippet: Optional[str] = None


@dataclass
class LoadTestResult:
    """Load test execution result."""
    test_file: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    requests_per_second: float
    duration: str
    success: bool
    error: Optional[str] = None


@dataclass
class QualityAnalysisResult:
    """Complete code quality analysis result."""
    workspace_root: str
    analyzed_files: List[str]
    total_issues: int
    issues_by_dimension: Dict[str, int]
    critical_issues: List[CodeQualityIssue]
    all_issues: List[CodeQualityIssue]
    analysis_summary: str


class LucidityAnalyzer:
    """Code quality analyzer using Lucidity MCP with hybrid connection strategy."""
    
    QUALITY_DIMENSIONS = [
        "unnecessary_complexity",
        "poor_abstractions", 
        "unintended_code_deletion",
        "hallucinated_components",
        "style_inconsistencies",
        "security_vulnerabilities",
        "performance_issues",
        "code_duplication",
        "incomplete_error_handling",
        "test_coverage_gaps"
    ]
    
    def __init__(self):
        """Initialize Lucidity analyzer with hybrid connection."""
        self.mcp_manager = _mcp_manager
        self.timeout = 30
    
    @property
    def is_available(self) -> bool:
        """Check if Lucidity MCP is available via hybrid approach."""
        return self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if Lucidity MCP is available via hybrid approach."""
        connection_info = self.mcp_manager.get_connection_info("lucidity")
        return connection_info["available"]
    
    def analyze_code(self, workspace_root: str, target_path: str = None,
                    focus_dimensions: List[str] = None) -> Dict[str, Any]:
        """Analyze code using Lucidity MCP with hybrid connection."""
        connection_info = self.mcp_manager.get_connection_info("lucidity")
        
        if not connection_info["available"]:
            logger.warning("Lucidity MCP not available, using native fallback")
            return self._analyze_native_fallback(workspace_root, target_path, focus_dimensions)
        
        try:
            # Use the connection (aggregator or individual server)
            server_url = connection_info["url"]
            method = connection_info["method"]
            
            logger.info(f"Using Lucidity MCP via {method}: {server_url}")
            
            # Prepare analysis request
            request_data = {
                "workspace_root": workspace_root,
                "target_path": target_path,
                "focus_dimensions": focus_dimensions or self.QUALITY_DIMENSIONS
            }
            
            response = requests.post(
                f"{server_url}/analyze",
                json=request_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                result["connection_method"] = method
                result["server_url"] = server_url
                return result
            else:
                logger.error(f"Lucidity analysis failed: {response.status_code}")
                return self._analyze_native_fallback(workspace_root, target_path, focus_dimensions)
                
        except Exception as e:
            logger.error(f"Error connecting to Lucidity MCP: {e}")
            return self._analyze_native_fallback(workspace_root, target_path, focus_dimensions)
    
    def _analyze_native_fallback(self, workspace_root: str, target_path: str = None,
                                focus_dimensions: List[str] = None) -> Dict[str, Any]:
        """Analyze code using native Python AST parsing and static analysis."""
        try:
            logger.info("Using native Python code analysis fallback")
            
            workspace_path = Path(workspace_root)
            if not workspace_path.exists():
                return {
                    "success": False,
                    "error": f"Workspace path does not exist: {workspace_root}",
                    "connection_method": "native"
                }
            
            # Determine files to analyze
            if target_path:
                target = Path(target_path)
                if target.is_absolute():
                    files_to_analyze = [target] if target.suffix == '.py' else []
                else:
                    files_to_analyze = [workspace_path / target] if (workspace_path / target).suffix == '.py' else []
            else:
                # Analyze all Python files in workspace
                files_to_analyze = list(workspace_path.rglob('*.py'))
            
            # Filter out common excluded directories
            excluded_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv'}
            files_to_analyze = [
                f for f in files_to_analyze 
                if not any(part in excluded_dirs for part in f.parts)
            ]
            
            if not files_to_analyze:
                return {
                    "success": True,
                    "analysis": {
                        "analysis_method": "native",
                        "workspace_root": workspace_root,
                        "total_files": 0,
                        "total_lines": 0,
                        "issues": [],
                        "metrics": {
                            "code_complexity": 0,
                            "maintainability_index": 100,
                            "technical_debt_minutes": 0
                        }
                    },
                    "connection_method": "native"
                }
            
            # Analyze files
            all_issues = []
            total_lines = 0
            complexity_scores = []
            
            for file_path in files_to_analyze:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = len(content.splitlines())
                        total_lines += lines
                    
                    # Parse AST
                    tree = ast.parse(content, filename=str(file_path))
                    
                    # Basic static analysis
                    issues = self._analyze_ast_tree(tree, file_path, content)
                    all_issues.extend(issues)
                    
                    # Calculate complexity
                    complexity = self._calculate_complexity(tree)
                    complexity_scores.append(complexity)
                    
                except SyntaxError as e:
                    all_issues.append({
                        "dimension": "syntax",
                        "severity": "error",
                        "file": str(file_path.relative_to(workspace_path)),
                        "line": e.lineno or 1,
                        "description": f"Syntax error: {e.msg}",
                        "suggestion": "Fix syntax error"
                    })
                except Exception as e:
                    logger.warning(f"Could not analyze {file_path}: {e}")
                    continue
            
            # Calculate metrics
            avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0
            maintainability_index = max(0, 100 - (avg_complexity * 10) - (len(all_issues) * 2))
            technical_debt = len(all_issues) * 5  # 5 minutes per issue estimate
            
            return {
                "success": True,
                "analysis": {
                    "analysis_method": "native",
                    "workspace_root": workspace_root,
                    "total_files": len(files_to_analyze),
                    "total_lines": total_lines,
                    "issues": all_issues,
                    "metrics": {
                        "code_complexity": round(avg_complexity, 2),
                        "maintainability_index": round(maintainability_index, 1),
                        "technical_debt_minutes": technical_debt
                    }
                },
                "connection_method": "native"
            }
                
        except Exception as e:
            logger.error(f"Native code analysis failed: {e}")
            return {
                "success": False,
                "error": f"Native analysis failed: {str(e)}",
                "connection_method": "native"
            }
    
    def _analyze_ast_tree(self, tree: ast.AST, file_path: Path, content: str) -> List[Dict[str, Any]]:
        """Analyze AST tree for common issues."""
        issues = []
        lines = content.splitlines()
        
        for node in ast.walk(tree):
            # Check for security issues
            if isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Attribute) and 
                    isinstance(node.func.value, ast.Name) and
                    node.func.value.id == 'subprocess' and
                    node.func.attr in ['run', 'call', 'Popen']):
                    
                    # Check for shell=True
                    for keyword in node.keywords:
                        if keyword.arg == 'shell' and isinstance(keyword.value, ast.Constant) and keyword.value.value:
                            issues.append({
                                "dimension": "security",
                                "severity": "high",
                                "file": str(file_path.name),
                                "line": node.lineno,
                                "description": "Use of shell=True in subprocess call creates security risk",
                                "suggestion": "Use shell=False and pass command as list"
                            })
                
                # Check for eval/exec usage
                if isinstance(node.func, ast.Name) and node.func.id in ['eval', 'exec']:
                    issues.append({
                        "dimension": "security", 
                        "severity": "critical",
                        "file": str(file_path.name),
                        "line": node.lineno,
                        "description": f"Use of {node.func.id}() creates code injection risk",
                        "suggestion": "Avoid eval/exec or use ast.literal_eval for safe evaluation"
                    })
            
            # Check for broad exception handling
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                issues.append({
                    "dimension": "maintainability",
                    "severity": "medium",
                    "file": str(file_path.name),
                    "line": node.lineno,
                    "description": "Bare except clause catches all exceptions",
                    "suggestion": "Catch specific exception types instead of using bare except"
                })
            
            # Check for long functions
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                if func_lines > 50:
                    issues.append({
                        "dimension": "maintainability",
                        "severity": "medium", 
                        "file": str(file_path.name),
                        "line": node.lineno,
                        "description": f"Function '{node.name}' is too long ({func_lines} lines)",
                        "suggestion": "Consider breaking down into smaller functions"
                    })
            
            # Check for too many arguments
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                arg_count = (len(node.args.args) + len(node.args.posonlyargs) + 
                            len(node.args.kwonlyargs) + (1 if node.args.vararg else 0) + 
                            (1 if node.args.kwarg else 0))
                if arg_count > 7:
                    issues.append({
                        "dimension": "maintainability",
                        "severity": "medium",
                        "file": str(file_path.name),
                        "line": node.lineno,
                        "description": f"Function '{node.name}' has too many parameters ({arg_count})",
                        "suggestion": "Consider using a configuration object or reducing parameters"
                    })
            
            # Check for long lines
            if hasattr(node, 'lineno') and node.lineno <= len(lines):
                line = lines[node.lineno - 1]
                if len(line) > 120:
                    issues.append({
                        "dimension": "style",
                        "severity": "low",
                        "file": str(file_path.name),
                        "line": node.lineno,
                        "description": f"Line too long ({len(line)} characters)",
                        "suggestion": "Break long lines for better readability"
                    })
        
        return issues
    
    def _calculate_complexity(self, tree: ast.AST) -> float:
        """Calculate cyclomatic complexity of AST tree."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            # Control flow structures add complexity
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.Try):
                complexity += len(node.handlers)
            elif isinstance(node, (ast.BoolOp)):
                complexity += len(node.values) - 1
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity += 1
        
        return complexity
    
    def analyze_with_git_diff(self, workspace_root: str) -> Dict[str, Any]:
        """Analyze git changes in workspace."""
        try:
            # Get git diff
            git_cmd = ["git", "diff", "--cached"]
            if not self._has_staged_changes(workspace_root):
                git_cmd = ["git", "diff", "HEAD~1"]
            
            result = subprocess.run(
                git_cmd,
                cwd=workspace_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": "Failed to get git diff",
                    "git_error": result.stderr
                }
            
            diff_content = result.stdout
            if not diff_content.strip():
                return {
                    "success": True,
                    "analysis": "No changes detected",
                    "diff_empty": True
                }
            
            # Analyze the diff content
            return self._analyze_diff_content(diff_content, workspace_root)
            
        except Exception as e:
            logger.error(f"Git diff analysis failed: {e}")
            return {
                "success": False,
                "error": f"Git analysis failed: {str(e)}"
            }
    
    def _has_staged_changes(self, workspace_root: str) -> bool:
        """Check if there are staged changes."""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=workspace_root,
                capture_output=True,
                text=True
            )
            return bool(result.stdout.strip())
        except:
            return False
    
    def _analyze_diff_content(self, diff_content: str, workspace_root: str) -> Dict[str, Any]:
        """Analyze diff content for quality issues."""
        # Fallback analysis when MCP server is not available
        issues = []
        
        # Simple pattern-based analysis
        lines = diff_content.split('\n')
        current_file = None
        line_number = 0
        
        for line in lines:
            if line.startswith('+++'):
                current_file = line[6:] if line.startswith('+++ b/') else line[4:]
                line_number = 0
                continue
            
            if line.startswith('@@'):
                # Extract line number from hunk header
                match = re.search(r'\+(\d+)', line)
                if match:
                    line_number = int(match.group(1))
                continue
            
            if line.startswith('+') and not line.startswith('+++'):
                line_number += 1
                added_line = line[1:]
                
                # Check for potential issues
                file_issues = self._check_line_for_issues(added_line, current_file, line_number)
                issues.extend(file_issues)
        
        return {
            "success": True,
            "analysis": {
                "total_issues": len(issues),
                "issues": [asdict(issue) for issue in issues],
                "analysis_method": "fallback_pattern_analysis"
            },
            "fallback_used": True
        }
    
    def _check_line_for_issues(self, line: str, file_path: str, line_number: int) -> List[CodeQualityIssue]:
        """Check a line for potential quality issues."""
        issues = []
        
        # Security patterns
        security_patterns = [
            (r'eval\s*\(', "security_vulnerabilities", "Use of eval() can be dangerous"),
            (r'exec\s*\(', "security_vulnerabilities", "Use of exec() can be dangerous"),
            (r'subprocess\.shell\s*=\s*True', "security_vulnerabilities", "Shell=True in subprocess can be risky"),
            (r'pickle\.loads?\s*\(', "security_vulnerabilities", "Pickle can execute arbitrary code"),
        ]
        
        # Performance patterns
        performance_patterns = [
            (r'\.append\s*\(.*\)\s*for.*in', "performance_issues", "List comprehension might be more efficient"),
            (r'for.*in.*range\s*\(\s*len\s*\(', "performance_issues", "Consider enumerate() instead"),
        ]
        
        # Complexity patterns  
        complexity_patterns = [
            (r'if.*and.*and.*and', "unnecessary_complexity", "Complex boolean condition"),
            (r'for.*for.*for.*for', "unnecessary_complexity", "Deeply nested loops"),
        ]
        
        # Error handling patterns
        error_patterns = [
            (r'except\s*:', "incomplete_error_handling", "Bare except clause catches all exceptions"),
            (r'except\s+Exception\s*:', "incomplete_error_handling", "Catching generic Exception"),
        ]
        
        all_patterns = [
            (*security_patterns, "Security"),
            (*performance_patterns, "Performance"), 
            (*complexity_patterns, "Complexity"),
            (*error_patterns, "Error Handling")
        ]
        
        for pattern_group in all_patterns:
            patterns = pattern_group[:-1]
            category = pattern_group[-1]
            
            for pattern, dimension, description in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(CodeQualityIssue(
                        dimension=dimension,
                        severity="medium",
                        file_path=file_path or "unknown",
                        line_number=line_number,
                        description=description,
                        recommendation=f"Review {category.lower()} implications",
                        code_snippet=line.strip()
                    ))
        
        return issues


class LocustLoadTester:
    """Load tester using Locust MCP server with hybrid connection strategy."""
    
    def __init__(self):
        """Initialize Locust load tester with hybrid connection."""
        self.mcp_manager = _mcp_manager
    
    def _check_availability(self) -> bool:
        """Check if Locust MCP is available via hybrid approach."""
        connection_info = self.mcp_manager.get_connection_info("locust")
        return connection_info["available"]
    
    def run_load_test(
        self,
        test_file: str,
        target_host: str = "http://localhost:8089",
        users: int = 3,
        spawn_rate: int = 1,
        runtime: str = "10s",
        headless: bool = True
    ) -> Dict[str, Any]:
        """Run a Locust load test using hybrid connection strategy."""
        try:
            connection_info = self.mcp_manager.get_connection_info("locust")
            
            if connection_info["method"] in ["aggregator", "individual"]:
                # Use MCP server
                payload = {
                    "method": "tools/call",
                    "params": {
                        "name": "run_load_test",
                        "arguments": {
                            "test_file": test_file,
                            "target_host": target_host,
                            "users": users,
                            "spawn_rate": spawn_rate,
                            "runtime": runtime,
                            "headless": headless
                        }
                    }
                }
                
                response = requests.post(
                    f"{connection_info['url']}/mcp",
                    json=payload,
                    timeout=300
                )
                
                if response.status_code == 200:
                    result = response.json()
                    result["connection_method"] = connection_info["method"]
                    return result
            
            # Fallback to native implementation
            return self._run_native_load_test(
                test_file, target_host, users, spawn_rate, runtime, headless
            )
            
        except Exception as e:
            logger.error(f"Load test failed: {e}")
            return {
                "success": False,
                "error": f"Load test failed: {str(e)}"
            }
    
    def create_test_script(
        self,
        target_url: str,
        test_name: str = "api_load_test",
        endpoints: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a Locust test script using hybrid connection strategy."""
        try:
            connection_info = self.mcp_manager.get_connection_info("locust")
            
            if connection_info["method"] in ["aggregator", "individual"]:
                # Use MCP server
                payload = {
                    "method": "tools/call",
                    "params": {
                        "name": "create_test_script",
                        "arguments": {
                            "target_url": target_url,
                            "test_name": test_name,
                            "endpoints": endpoints
                        }
                    }
                }
                
                response = requests.post(
                    f"{connection_info['url']}/mcp",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    result["connection_method"] = connection_info["method"]
                    return result
            
            # Fallback to native implementation
            return self._create_native_test_script(target_url, test_name, endpoints)
            
        except Exception as e:
            logger.error(f"Test script creation failed: {e}")
            return {
                "success": False,
                "error": f"Test script creation failed: {str(e)}"
            }
    
    def _run_native_load_test(
        self,
        test_file: str,
        target_host: str,
        users: int,
        spawn_rate: int,
        runtime: str,
        headless: bool
    ) -> Dict[str, Any]:
        """Run a Locust load test using native implementation."""
        try:
            # Build Locust command
            cmd = [
                "locust",
                "-f", test_file,
                "--host", target_host,
                "--users", str(users),
                "--spawn-rate", str(spawn_rate),
                "--run-time", runtime
            ]
            
            if headless:
                cmd.append("--headless")
            
            # Run the test
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Locust returns exit code 1 when there are test failures, but this is still valid execution
            # Only treat as error if there's no output or explicit error messages
            if result.returncode in [0, 1]:  # 0 = success, 1 = test failures (but valid execution)
                parsed_results = self._parse_locust_output(result.stdout, test_file, runtime)
                if parsed_results or "Starting Locust" in result.stdout:
                    return {
                        "success": True,
                        "load_test_results": {
                            "test_method": "native",
                            "output": result.stdout,
                            "metrics": parsed_results,
                            "exit_code": result.returncode
                        },
                        "connection_method": "native"
                    }
            
            # True error case
            return {
                "success": False,
                "error": f"Locust execution failed: {result.stderr or result.stdout}",
                "connection_method": "native"
            }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Test execution timed out",
                "connection_method": "native"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Native load test failed: {str(e)}",
                "connection_method": "native"
            }
    
    def _create_native_test_script(
        self,
        target_url: str,
        test_name: str = "api_load_test", 
        endpoints: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a Locust test script using native implementation."""
        try:
            if not endpoints:
                endpoints = ["/", "/health", "/api/status"]
            
            # Generate test content
            test_content = f'''
from locust import HttpUser, task, between
import time
import json

class {test_name.replace("_", "").title()}User(HttpUser):
    wait_time = between(1, 3)
    host = "{target_url}"
    
    def on_start(self):
        """Called when a user starts running."""
        pass
    
    def on_stop(self):
        """Called when a user stops running."""
        pass
'''
            
            # Add tasks for each endpoint
            for i, endpoint in enumerate(endpoints, 1):
                task_name = endpoint.replace("/", "_").replace("-", "_").strip("_")
                if not task_name:
                    task_name = "root"
                
                weight = 3 if endpoint in ["/", "/health"] else 1
                
                test_content += f'''
    @task({weight})
    def test_{task_name}(self):
        """Test {endpoint} endpoint."""
        with self.client.get("{endpoint}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {{response.status_code}}")
'''
            
            # Add error handling task
            test_content += '''
    @task(1)
    def test_error_handling(self):
        """Test error handling."""
        with self.client.get("/nonexistent", catch_response=True) as response:
            # We expect this to fail, so don't mark as failure
            if response.status_code == 404:
                response.success()
'''
            
            # Create temporary file
            test_file = tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.py', 
                prefix=f'{test_name}_',
                delete=False
            )
            
            with test_file as f:
                f.write(test_content)
            
            return {
                "success": True,
                "test_file_path": test_file.name,
                "test_content": test_content,
                "target_url": target_url,
                "endpoints_included": endpoints,
                "usage_instructions": f"Run with: locust -f {test_file.name} --host {target_url}",
                "connection_method": "native"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Test script creation failed: {str(e)}",
                "connection_method": "native"
            }
    
    def _parse_locust_output(self, output: str, test_file: str, runtime: str) -> LoadTestResult:
        """Parse Locust output to extract test results."""
        try:
            # Default values
            total_requests = 0
            successful_requests = 0
            failed_requests = 0
            avg_response_time = 0.0
            min_response_time = 0.0
            max_response_time = 0.0
            requests_per_second = 0.0
            
            lines = output.split('\n')
            
            # Look for statistics table
            for i, line in enumerate(lines):
                if 'Name' in line and 'Reqs' in line and 'Fails' in line:
                    # Found stats header, parse following lines
                    for j in range(i + 1, min(i + 10, len(lines))):
                        stats_line = lines[j].strip()
                        if not stats_line or stats_line.startswith('-'):
                            continue
                        
                        # Parse statistics line
                        parts = stats_line.split()
                        if len(parts) >= 8:
                            try:
                                reqs = int(parts[1])
                                fails = int(parts[2])
                                total_requests += reqs
                                failed_requests += fails
                                successful_requests = total_requests - failed_requests
                                
                                # Parse response times
                                if len(parts) >= 6:
                                    avg_response_time = float(parts[3])
                                    min_response_time = float(parts[4])
                                    max_response_time = float(parts[5])
                                
                                # Parse RPS
                                if len(parts) >= 8:
                                    requests_per_second = float(parts[7])
                                    
                            except ValueError:
                                continue
            
            return LoadTestResult(
                test_file=test_file,
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                average_response_time=avg_response_time,
                min_response_time=min_response_time,
                max_response_time=max_response_time,
                requests_per_second=requests_per_second,
                duration=runtime,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Failed to parse Locust output: {e}")
            return LoadTestResult(
                test_file=test_file,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                average_response_time=0.0,
                min_response_time=0.0,
                max_response_time=0.0,
                requests_per_second=0.0,
                duration=runtime,
                success=False,
                error="Failed to parse test results"
            )
    
    def create_simple_test(self, target_url: str, test_name: str = "simple_test") -> str:
        """Create a simple Locust test file."""
        test_content = f'''
from locust import HttpUser, task, between
import time

class {test_name.title()}User(HttpUser):
    wait_time = between(1, 3)
    host = "{target_url}"
    
    @task
    def index_page(self):
        self.client.get("/")
    
    @task(2)
    def health_check(self):
        self.client.get("/health")
        
    @task
    def api_endpoint(self):
        self.client.get("/api/status")
'''
        
        # Create temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_content)
            return f.name


# Initialize analyzers
_lucidity_analyzer = None
_locust_tester = None


def get_lucidity_analyzer() -> LucidityAnalyzer:
    """Get shared Lucidity analyzer instance."""
    global _lucidity_analyzer
    if _lucidity_analyzer is None:
        _lucidity_analyzer = LucidityAnalyzer()
    return _lucidity_analyzer


def get_locust_tester() -> LocustLoadTester:
    """Get shared Locust tester instance."""
    global _locust_tester
    if _locust_tester is None:
        _locust_tester = LocustLoadTester()
    return _locust_tester


@tool
def analyze_code_quality(
    workspace_root: str,
    target_path: Optional[str] = None,
    focus_dimensions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Analyze code quality using Lucidity MCP for comprehensive quality assessment.
    
    Args:
        workspace_root: Root directory of the workspace/repository
        target_path: Optional specific file/directory to analyze
        focus_dimensions: Optional list of quality dimensions to focus on
        
    Returns:
        Dict with quality analysis results
    """
    try:
        analyzer = get_lucidity_analyzer()
        
        # Use hybrid approach - analyzer handles aggregator/individual/native fallback
        result = analyzer.analyze_code(workspace_root, target_path, focus_dimensions)
        
        if result.get("success"):
            logger.info(f"Code quality analysis completed using {result.get('connection_method', 'native')} method")
        
        return result
        
    except Exception as e:
        logger.error(f"Code quality analysis failed: {e}")
        return {
            "success": False,
            "error": f"Analysis failed: {str(e)}"
        }


@tool
def run_load_test(
    test_file: str,
    target_host: str = "http://localhost:8080",
    users: int = 10,
    spawn_rate: int = 2,
    runtime: str = "30s",
    headless: bool = True
) -> Dict[str, Any]:
    """Run load testing using Locust MCP server.
    
    Args:
        test_file: Path to Locust test file (.py)
        target_host: Target host URL to test
        users: Number of concurrent users to simulate
        spawn_rate: Rate at which users are spawned per second
        runtime: Test duration (e.g., "30s", "2m", "1h")
        headless: Run in headless mode (True) or with UI (False)
        
    Returns:
        Dict with load test results
    """
    try:
        tester = get_locust_tester()
        
        # Validate test file exists
        if not os.path.exists(test_file):
            return {
                "success": False,
                "error": f"Test file not found: {test_file}"
            }
        
        # Run the load test
        result = tester.run_load_test(
            test_file=test_file,
            target_host=target_host,
            users=users,
            spawn_rate=spawn_rate,
            runtime=runtime,
            headless=headless
        )
        
        if result.get("success"):
            logger.info(f"Load test completed using {result.get('connection_method', 'native')} method")
        
        return result
        
    except Exception as e:
        logger.error(f"Load test execution failed: {e}")
        return {
            "success": False,
            "error": f"Load test failed: {str(e)}"
        }


@tool
def create_load_test_script(
    target_url: str,
    test_name: str = "api_load_test",
    endpoints: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create a Locust load test script for the specified target.
    
    Args:
        target_url: Base URL of the target application
        test_name: Name for the test class
        endpoints: List of endpoint paths to test (e.g., ["/api/users", "/health"])
        
    Returns:
        Dict with created test file path and content
    """
    try:
        tester = get_locust_tester()
        
        # Use the hybrid connection to create test script
        result = tester.create_test_script(
            target_url=target_url,
            test_name=test_name,
            endpoints=endpoints or ["/", "/health", "/api/status"]
        )
        
        if result.get("success"):
            logger.info(f"Load test script created using {result.get('connection_method', 'native')} method")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to create load test script: {e}")
        return {
            "success": False,
            "error": f"Test script creation failed: {str(e)}"
        }


@tool
def validate_test_environment(
    workspace_root: str,
    target_url: Optional[str] = None
) -> Dict[str, Any]:
    """Validate the testing environment and dependencies.
    
    Args:
        workspace_root: Root directory of the workspace
        target_url: Optional target URL to check connectivity
        
    Returns:
        Dict with validation results
    """
    try:
        validation_results = {
            "git_available": False,
            "git_repository": False,
            "has_changes": False,
            "locust_available": False,
            "lucidity_available": False,
            "target_connectivity": None,
            "python_version": None,
            "workspace_valid": False
        }
        
        # Check workspace
        if os.path.exists(workspace_root) and os.path.isdir(workspace_root):
            validation_results["workspace_valid"] = True
        
        # Check Git
        try:
            result = subprocess.run(
                ["git", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            validation_results["git_available"] = result.returncode == 0
            
            if validation_results["git_available"] and validation_results["workspace_valid"]:
                # Check if it's a git repository
                result = subprocess.run(
                    ["git", "status"], 
                    cwd=workspace_root,
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                validation_results["git_repository"] = result.returncode == 0
                
                if validation_results["git_repository"]:
                    # Check for changes
                    result = subprocess.run(
                        ["git", "diff", "--name-only"], 
                        cwd=workspace_root,
                        capture_output=True, 
                        text=True, 
                        timeout=5
                    )
                    validation_results["has_changes"] = bool(result.stdout.strip())
                    
        except:
            pass
        
        # Check Locust
        tester = get_locust_tester()
        validation_results["locust_available"] = tester.is_available
        
        # Check Lucidity
        analyzer = get_lucidity_analyzer()
        validation_results["lucidity_available"] = analyzer.is_available
        
        # Check Python version
        try:
            import sys
            validation_results["python_version"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        except:
            pass
        
        # Check target connectivity
        if target_url:
            try:
                response = requests.get(target_url, timeout=10)
                validation_results["target_connectivity"] = {
                    "reachable": True,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds()
                }
            except Exception as e:
                validation_results["target_connectivity"] = {
                    "reachable": False,
                    "error": str(e)
                }
        
        # Generate recommendations
        recommendations = []
        
        if not validation_results["git_available"]:
            recommendations.append("Install Git for code change analysis")
        
        if not validation_results["locust_available"]:
            recommendations.append("Install Locust for load testing: pip install locust")
        
        if not validation_results["lucidity_available"]:
            recommendations.append("Install Lucidity MCP for code quality analysis")
        
        if target_url and validation_results["target_connectivity"] and not validation_results["target_connectivity"]["reachable"]:
            recommendations.append("Target URL is not reachable - check network connectivity")
        
        return {
            "success": True,
            "validation_results": validation_results,
            "recommendations": recommendations,
            "overall_status": "ready" if all([
                validation_results["workspace_valid"],
                validation_results["git_available"],
                validation_results["locust_available"] or validation_results["lucidity_available"]
            ]) else "needs_setup"
        }
        
    except Exception as e:
        logger.error(f"Environment validation failed: {e}")
        return {
            "success": False,
            "error": f"Validation failed: {str(e)}"
        }


def _generate_performance_recommendations(result: LoadTestResult) -> List[str]:
    """Generate performance recommendations based on test results."""
    recommendations = []
    
    if not result.success:
        recommendations.append("Fix test execution issues before analyzing performance")
        return recommendations
    
    # Success rate recommendations
    success_rate = (result.successful_requests / max(result.total_requests, 1)) * 100
    if success_rate < 95:
        recommendations.append(f"Success rate is {success_rate:.1f}% - investigate failed requests")
    
    # Response time recommendations
    if result.average_response_time > 1000:  # > 1 second
        recommendations.append("Average response time is high - consider performance optimization")
    
    if result.max_response_time > result.average_response_time * 3:
        recommendations.append("High response time variance detected - check for intermittent issues")
    
    # Throughput recommendations
    if result.requests_per_second < 10:
        recommendations.append("Low throughput detected - consider scaling or optimization")
    
    # Request volume recommendations
    if result.total_requests < 100:
        recommendations.append("Consider running longer tests for more reliable results")
    
    if not recommendations:
        recommendations.append("Performance metrics look good! Consider testing with higher load.")
    
    return recommendations


# Export all tools
__all__ = [
    'LucidityAnalyzer',
    'LocustLoadTester', 
    'CodeQualityIssue',
    'LoadTestResult',
    'QualityAnalysisResult',
    'analyze_code_quality',
    'run_load_test',
    'create_load_test_script',
    'validate_test_environment'
]
