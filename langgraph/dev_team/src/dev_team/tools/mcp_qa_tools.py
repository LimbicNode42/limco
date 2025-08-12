"""MCP QA and Testing Tools

This module provides QA and testing capabilities using:
- hyperb1iss/lucidity-mcp for code quality analysis
- qainsights/locust-mcp-server for load/performance testing
"""

import os
import re
import json
import subprocess
import tempfile
import time
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import logging
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


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
    """Code quality analyzer using Lucidity MCP."""
    
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
    
    def __init__(self, server_url: str = "http://localhost:6969"):
        """Initialize Lucidity analyzer."""
        self.server_url = server_url
        self.timeout = 30
        self.is_available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if Lucidity MCP server is available."""
        try:
            # Check if lucidity-mcp command exists
            result = subprocess.run(
                ["lucidity-mcp", "--help"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # Try to check if server is running via HTTP
            try:
                response = requests.get(f"{self.server_url}/health", timeout=2)
                return response.status_code == 200
            except:
                return False
    
    def start_server(self, port: int = 6969) -> bool:
        """Start Lucidity MCP server in SSE mode."""
        try:
            # Start server in background
            cmd = [
                "lucidity-mcp", 
                "--transport", "sse",
                "--host", "127.0.0.1",
                "--port", str(port)
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a moment for server to start
            time.sleep(2)
            
            # Check if server is responsive
            try:
                response = requests.get(f"http://127.0.0.1:{port}/health", timeout=5)
                if response.status_code == 200:
                    self.is_available = True
                    return True
            except:
                pass
                
            return False
            
        except Exception as e:
            logger.error(f"Failed to start Lucidity server: {e}")
            return False
    
    def analyze_changes(self, workspace_root: str, path: Optional[str] = None) -> Dict[str, Any]:
        """Analyze code changes using Lucidity."""
        if not self.is_available:
            return {
                "success": False,
                "error": "Lucidity analyzer not available",
                "fallback_used": True
            }
        
        try:
            # Prepare analysis request
            payload = {
                "method": "tools/call",
                "params": {
                    "name": "analyze_changes",
                    "arguments": {
                        "workspace_root": workspace_root,
                        "path": path
                    }
                }
            }
            
            response = requests.post(
                f"{self.server_url}/mcp",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "analysis": result.get("result", {}),
                    "method": "lucidity_mcp"
                }
            else:
                return {
                    "success": False,
                    "error": f"Server returned status {response.status_code}",
                    "fallback_used": False
                }
                
        except Exception as e:
            logger.error(f"Lucidity analysis failed: {e}")
            return {
                "success": False,
                "error": f"Analysis request failed: {str(e)}",
                "fallback_used": False
            }
    
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
    """Load tester using Locust MCP server."""
    
    def __init__(self):
        """Initialize Locust load tester."""
        self.is_available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if Locust is available."""
        try:
            result = subprocess.run(
                ["locust", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def run_load_test(
        self,
        test_file: str,
        headless: bool = True,
        host: str = "http://localhost:8089",
        runtime: str = "10s",
        users: int = 3,
        spawn_rate: int = 1
    ) -> LoadTestResult:
        """Run a Locust load test."""
        if not self.is_available:
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
                error="Locust not available"
            )
        
        try:
            # Build Locust command
            cmd = [
                "locust",
                "-f", test_file,
                "--host", host,
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
            
            if result.returncode == 0:
                return self._parse_locust_output(result.stdout, test_file, runtime)
            else:
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
                    error=f"Locust execution failed: {result.stderr}"
                )
                
        except subprocess.TimeoutExpired:
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
                error="Test execution timed out"
            )
        except Exception as e:
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
                error=f"Test execution failed: {str(e)}"
            )
    
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
        
        # First try MCP server analysis
        if analyzer.is_available:
            result = analyzer.analyze_changes(workspace_root, target_path)
        else:
            # Try to start server if not available
            if analyzer.start_server():
                result = analyzer.analyze_changes(workspace_root, target_path)
            else:
                # Fall back to git diff analysis
                result = analyzer.analyze_with_git_diff(workspace_root)
        
        # Enhance results with filtering if focus dimensions specified
        if focus_dimensions and result.get("success"):
            analysis = result.get("analysis", {})
            if isinstance(analysis, dict) and "issues" in analysis:
                filtered_issues = [
                    issue for issue in analysis["issues"]
                    if issue.get("dimension") in focus_dimensions
                ]
                analysis["issues"] = filtered_issues
                analysis["filtered_by_dimensions"] = focus_dimensions
                analysis["total_issues"] = len(filtered_issues)
        
        return {
            "success": result.get("success", False),
            "workspace_root": workspace_root,
            "target_path": target_path,
            "analysis": result.get("analysis", {}),
            "error": result.get("error"),
            "method_used": result.get("method", "fallback"),
            "fallback_used": result.get("fallback_used", False),
            "available_dimensions": analyzer.QUALITY_DIMENSIONS
        }
        
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
            headless=headless,
            host=target_host,
            runtime=runtime,
            users=users,
            spawn_rate=spawn_rate
        )
        
        return {
            "success": result.success,
            "test_results": asdict(result),
            "performance_summary": {
                "total_requests": result.total_requests,
                "success_rate": (result.successful_requests / max(result.total_requests, 1)) * 100,
                "average_response_time": result.average_response_time,
                "requests_per_second": result.requests_per_second,
                "duration": result.duration
            },
            "recommendations": _generate_performance_recommendations(result),
            "error": result.error
        }
        
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
            "usage_instructions": f"Run with: locust -f {test_file.name} --host {target_url}"
        }
        
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
