"""GitHub MCP Server Integration for LangGraph agents with Hybrid Connection Strategy."""

import os
import asyncio
import time
import threading
import subprocess
import requests
from typing import List, Optional, Dict, Any
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import Tool, tool
import logging

logger = logging.getLogger(__name__)

# MCP Server Configuration - Hybrid Approach
# Primary: Connect to MCP Aggregator/Proxy
# Secondary: Start individual MCP servers
MCP_GITHUB_CONFIG = {
    "aggregator": {
        "enabled": True,
        "url": os.getenv("MCP_AGGREGATOR_URL", "http://localhost:8080"),
        "timeout": 5,
        "github_endpoint": "/github",
    },
    "individual_servers": {
        "github-mcp-server": {
            "port": int(os.getenv("GITHUB_MCP_SERVER_PORT", "6978")),
            "host": "127.0.0.1",
            "start_command": ["github-mcp-server"],
            "health_endpoint": "/health"
        },
    },
    "fallback_native": True,
    "startup_timeout": 30,
    "health_check_interval": 10
}


class MCPGitHubConnectionManager:
    """Manages hybrid MCP connections for GitHub operations - aggregator first, individual servers as fallback."""
    
    def __init__(self):
        self.config = MCP_GITHUB_CONFIG
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
            # Use very short timeout to prevent hanging
            response = requests.get(f"{url}/health", timeout=1)
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
            # For GitHub MCP server, we need to use stdio transport, not HTTP
            # The server runs as a process communicating via stdin/stdout
            env = os.environ.copy()
            env["GITHUB_PERSONAL_ACCESS_TOKEN"] = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "")
            
            logger.info(f"Starting {server_name} MCP server: {' '.join(config['start_command'])}")
            
            # Use DEVNULL to prevent hanging - GitHub MCP server is stdio-based
            process = subprocess.Popen(
                config["start_command"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                text=True,
                env=env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # Store process reference
            with self._lock:
                self.server_processes[server_name] = process
            
            # Give server a moment to start
            time.sleep(0.5)  # Shorter wait since we can't communicate anyway
            
            # For stdio servers, we can't do HTTP health checks
            # Instead, check if process is still running
            if process.poll() is None:
                logger.info(f"{server_name} MCP server started successfully")
                return True
            else:
                logger.warning(f"{server_name} MCP server may have failed to start")
                return False  # Don't cleanup, process might be starting
                
        except Exception as e:
            logger.error(f"Failed to start {server_name} MCP server: {e}")
            return False
    
    def _check_command_exists(self, command: str) -> bool:
        """Check if a command exists in the system PATH."""
        try:
            # For github-mcp-server, first check if it's in project directory
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
            binary_path = os.path.join(project_root, "github-mcp-server.exe")
            
            if os.path.exists(binary_path):
                return True
                
            # Try running the command to check if it exists
            subprocess.run([command, "--version"], capture_output=True, timeout=5)
            return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def check_individual_server_health(self, server_name: str) -> bool:
        """Check health of individual MCP server."""
        with self._lock:
            if server_name in self.server_processes:
                process = self.server_processes[server_name]
                # For stdio servers, health is whether process is still running
                return process.poll() is None
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
        """Get connection info for a server type."""
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
            if not self.check_individual_server_health("github-mcp-server"):
                if self.start_individual_server("github-mcp-server"):
                    return {
                        "method": "individual",
                        "url": None,  # stdio transport, no URL
                        "available": True,
                        "transport": "stdio"
                    }
            else:
                return {
                    "method": "individual", 
                    "url": None,  # stdio transport, no URL
                    "available": True,
                    "transport": "stdio"
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
_mcp_github_manager = MCPGitHubConnectionManager()

# Alias for consistent testing
MCPConnectionManager = MCPGitHubConnectionManager

class GitHubMCPClient:
    """Client for GitHub MCP Server integration with hybrid connection strategy."""
    
    def __init__(self, github_token: str, server_path: str = None, toolsets: Optional[List[str]] = None):
        """
        Initialize GitHub MCP client.
        
        Args:
            github_token: GitHub Personal Access Token
            server_path: Path to the github-mcp-server executable
            toolsets: List of toolsets to enable (defaults to repos, issues, pull_requests)
        """
        self.github_token = github_token
        self.server_path = server_path or self._get_default_server_path()
        self.toolsets = toolsets or ["repos", "issues", "pull_requests", "context"]
        self._client = None
        self._tools = None
        self.mcp_manager = _mcp_github_manager
        
    def _get_default_server_path(self) -> str:
        """Get the default path to the GitHub MCP server executable."""
        # Try to find the binary in the project directory
        # Path: dev_team/src/dev_team/github_mcp.py -> limco/github-mcp-server.exe
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        binary_path = os.path.join(project_root, "github-mcp-server.exe")
        
        if os.path.exists(binary_path):
            return os.path.abspath(binary_path)
        
        # Fallback to looking for it in PATH
        return "github-mcp-server"
    
    async def _initialize_client(self):
        """Initialize the MCP client using hybrid connection strategy."""
        if self._client is None:
            connection_info = self.mcp_manager.get_connection_info("github")
            
            if connection_info["method"] == "aggregator":
                # Use aggregator connection
                logger.info("Using MCP aggregator for GitHub operations")
                try:
                    # For aggregator, we'd use HTTP calls directly in get_tools()
                    self._connection_method = "aggregator"
                    self._connection_url = connection_info["url"]
                    return
                except Exception as e:
                    logger.warning(f"Aggregator connection failed: {e}, falling back to individual server")
            
            if connection_info["method"] == "individual":
                # Use individual MCP server
                logger.info("Using individual GitHub MCP server")
                try:
                    # Prepare environment variables
                    env = {
                        "GITHUB_PERSONAL_ACCESS_TOKEN": self.github_token,
                        "GITHUB_TOOLSETS": ",".join(self.toolsets)
                    }
                    
                    # Add current environment
                    env.update(os.environ)
                    
                    self._client = MultiServerMCPClient({
                        "github": {
                            "command": self.server_path,
                            "args": ["stdio"],
                            "transport": "stdio",
                            "env": env
                        }
                    })
                    
                    self._connection_method = "individual"
                    logger.info(f"Initialized GitHub MCP client with toolsets: {self.toolsets}")
                    return
                except Exception as e:
                    logger.warning(f"Individual MCP server failed: {e}, falling back to native")
            
            # Fallback to native implementation
            logger.info("Using native GitHub implementation")
            self._connection_method = "native"
            self._client = None
    
    async def get_tools(self) -> List[Tool]:
        """Get all available GitHub tools using hybrid connection strategy."""
        if self._tools is None:
            await self._initialize_client()
            
            try:
                if hasattr(self, '_connection_method'):
                    if self._connection_method == "aggregator":
                        # Use aggregator HTTP API
                        self._tools = await self._get_tools_via_aggregator()
                    elif self._connection_method == "individual":
                        # Use individual MCP server
                        self._tools = await self._get_tools_via_mcp()
                    else:
                        # Use native implementation
                        self._tools = self._get_tools_native()
                else:
                    # Fallback to native
                    self._tools = self._get_tools_native()
                
                logger.info(f"Retrieved {len(self._tools)} GitHub tools via {getattr(self, '_connection_method', 'native')}")
                
                # Log available tools for debugging
                if self._tools:
                    tool_names = [tool.name for tool in self._tools]
                    logger.debug(f"Available GitHub tools: {tool_names}")
                
            except Exception as e:
                logger.error(f"Failed to get GitHub tools: {e}")
                # Final fallback to native
                logger.info("Falling back to native GitHub implementation")
                self._tools = self._get_tools_native()
        
        return self._tools
    
    async def _get_tools_via_aggregator(self) -> List[Tool]:
        """Get tools via MCP aggregator."""
        try:
            # Make HTTP request to aggregator
            response = requests.post(
                f"{self._connection_url}/tools/list",
                json={"toolsets": self.toolsets},
                timeout=10
            )
            
            if response.status_code == 200:
                tools_data = response.json()
                # Convert to LangChain tools
                tools = []
                for tool_data in tools_data.get("tools", []):
                    tools.append(self._create_tool_from_data(tool_data))
                return tools
            else:
                raise Exception(f"Aggregator returned status {response.status_code}")
                
        except Exception as e:
            logger.error(f"Aggregator tool retrieval failed: {e}")
            raise
    
    async def _get_tools_via_mcp(self) -> List[Tool]:
        """Get tools via individual MCP server."""
        try:
            tools = await self._client.get_tools()
            return tools
        except Exception as e:
            logger.error(f"Individual MCP server tool retrieval failed: {e}")
            raise
    
    def _get_tools_native(self) -> List[Tool]:
        """Get tools using native GitHub implementation."""
        logger.info("Using native GitHub tools implementation")
        
        # Return basic GitHub tools using native implementation
        return [
            self._create_github_repo_tool(),
            self._create_github_issue_tool(),
            self._create_github_search_tool(),
            self._create_github_file_tool()
        ]
    
    def _create_tool_from_data(self, tool_data: Dict[str, Any]) -> Tool:
        """Create a LangChain tool from aggregator data."""
        def tool_func(**kwargs):
            # Make request to aggregator to execute tool
            response = requests.post(
                f"{self._connection_url}/tools/execute",
                json={
                    "tool": tool_data["name"],
                    "arguments": kwargs
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                result["connection_method"] = "aggregator"
                return result
            else:
                return {
                    "success": False,
                    "error": f"Tool execution failed: {response.status_code}",
                    "connection_method": "aggregator"
                }
        
        return Tool(
            name=tool_data["name"],
            description=tool_data.get("description", "GitHub tool via aggregator"),
            func=tool_func
        )
    
    def _create_github_repo_tool(self) -> Tool:
        """Create native GitHub repository tool."""
        @tool
        def github_repository_info(owner: str, repo: str) -> Dict[str, Any]:
            """Get information about a GitHub repository.
            
            Args:
                owner: Repository owner/organization
                repo: Repository name
            """
            try:
                import requests
                
                headers = {}
                if self.github_token:
                    headers["Authorization"] = f"token {self.github_token}"
                
                response = requests.get(
                    f"https://api.github.com/repos/{owner}/{repo}",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "connection_method": "native",
                        "repository": {
                            "name": data["name"],
                            "full_name": data["full_name"],
                            "description": data.get("description"),
                            "language": data.get("language"),
                            "stars": data["stargazers_count"],
                            "forks": data["forks_count"],
                            "open_issues": data["open_issues_count"],
                            "created_at": data["created_at"],
                            "updated_at": data["updated_at"],
                            "clone_url": data["clone_url"],
                            "homepage": data.get("homepage")
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to fetch repository: {response.status_code}",
                        "connection_method": "native"
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Repository lookup failed: {str(e)}",
                    "connection_method": "native"
                }
        
        return github_repository_info
    
    def _create_github_issue_tool(self) -> Tool:
        """Create native GitHub issues tool.""" 
        @tool
        def github_list_issues(owner: str, repo: str, state: str = "open", limit: int = 10) -> Dict[str, Any]:
            """List issues for a GitHub repository.
            
            Args:
                owner: Repository owner/organization
                repo: Repository name
                state: Issue state (open, closed, all)
                limit: Maximum number of issues to return
            """
            try:
                import requests
                
                headers = {}
                if self.github_token:
                    headers["Authorization"] = f"token {self.github_token}"
                
                params = {
                    "state": state,
                    "per_page": min(limit, 100)
                }
                
                response = requests.get(
                    f"https://api.github.com/repos/{owner}/{repo}/issues",
                    headers=headers,
                    params=params,
                    timeout=10
                )
                
                if response.status_code == 200:
                    issues = response.json()
                    return {
                        "success": True,
                        "connection_method": "native",
                        "issues": [
                            {
                                "number": issue["number"],
                                "title": issue["title"],
                                "state": issue["state"],
                                "user": issue["user"]["login"],
                                "created_at": issue["created_at"],
                                "updated_at": issue["updated_at"],
                                "body": issue.get("body", "")[:500]  # Truncate body
                            }
                            for issue in issues[:limit]
                        ]
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to fetch issues: {response.status_code}",
                        "connection_method": "native"
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Issue lookup failed: {str(e)}",
                    "connection_method": "native"
                }
        
        return github_list_issues
    
    def _create_github_search_tool(self) -> Tool:
        """Create native GitHub search tool."""
        @tool
        def github_search_repositories(query: str, sort: str = "stars", limit: int = 10) -> Dict[str, Any]:
            """Search GitHub repositories.
            
            Args:
                query: Search query
                sort: Sort order (stars, forks, updated)
                limit: Maximum number of results
            """
            try:
                import requests
                
                headers = {}
                if self.github_token:
                    headers["Authorization"] = f"token {self.github_token}"
                
                params = {
                    "q": query,
                    "sort": sort,
                    "per_page": min(limit, 100)
                }
                
                response = requests.get(
                    "https://api.github.com/search/repositories",
                    headers=headers,
                    params=params,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "connection_method": "native",
                        "total_count": data["total_count"],
                        "repositories": [
                            {
                                "name": repo["name"],
                                "full_name": repo["full_name"],
                                "description": repo.get("description"),
                                "language": repo.get("language"),
                                "stars": repo["stargazers_count"],
                                "forks": repo["forks_count"],
                                "clone_url": repo["clone_url"]
                            }
                            for repo in data["items"][:limit]
                        ]
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Search failed: {response.status_code}",
                        "connection_method": "native"
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Search failed: {str(e)}",
                    "connection_method": "native"
                }
        
        return github_search_repositories
    
    def _create_github_file_tool(self) -> Tool:
        """Create native GitHub file operations tool."""
        @tool
        def github_get_file_content(owner: str, repo: str, path: str, ref: str = "main") -> Dict[str, Any]:
            """Get content of a file from GitHub repository.
            
            Args:
                owner: Repository owner/organization
                repo: Repository name
                path: File path in repository
                ref: Branch/commit reference (default: main)
            """
            try:
                import requests
                import base64
                
                headers = {}
                if self.github_token:
                    headers["Authorization"] = f"token {self.github_token}"
                
                response = requests.get(
                    f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
                    headers=headers,
                    params={"ref": ref},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("encoding") == "base64":
                        content = base64.b64decode(data["content"]).decode("utf-8")
                    else:
                        content = data.get("content", "")
                    
                    return {
                        "success": True,
                        "connection_method": "native",
                        "file": {
                            "name": data["name"],
                            "path": data["path"],
                            "size": data["size"],
                            "content": content,
                            "sha": data["sha"],
                            "download_url": data.get("download_url")
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to fetch file: {response.status_code}",
                        "connection_method": "native"
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "error": f"File lookup failed: {str(e)}",
                    "connection_method": "native"
                }
        
        return github_get_file_content
    
    async def get_repository_tools(self) -> List[Tool]:
        """Get tools specifically for repository operations."""
        all_tools = await self.get_tools()
        
        # Filter tools related to repository operations
        repo_keywords = [
            "create_repository", "repository", "repo", "create", "fork",
            "clone", "branch", "commit", "push", "pull"
        ]
        
        repo_tools = []
        for tool in all_tools:
            tool_name_lower = tool.name.lower()
            if any(keyword in tool_name_lower for keyword in repo_keywords):
                repo_tools.append(tool)
        
        logger.info(f"Found {len(repo_tools)} repository-related tools")
        return repo_tools
    
    async def close(self):
        """Close the MCP client."""
        if self._client:
            # The MCP client should handle cleanup automatically
            pass
        
        # Cleanup connection manager
        self.mcp_manager.cleanup()


# Hybrid tool wrappers for direct use
@tool
def github_get_repository_info(owner: str, repo: str, github_token: str = None) -> Dict[str, Any]:
    """Get information about a GitHub repository using hybrid MCP strategy.
    
    Args:
        owner: Repository owner/organization
        repo: Repository name
        github_token: GitHub token (optional, uses env var if not provided)
    """
    try:
        if not github_token:
            github_token = get_github_token()
        
        client = GitHubMCPClient(github_token)
        
        # This will use the hybrid strategy automatically
        connection_info = client.mcp_manager.get_connection_info("github")
        
        if connection_info["method"] == "aggregator":
            # Use aggregator
            response = requests.post(
                f"{connection_info['url']}/tools/execute",
                json={
                    "tool": "get_repository",
                    "arguments": {"owner": owner, "repo": repo}
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                result["connection_method"] = "aggregator"
                return result
            else:
                logger.warning("Aggregator failed, falling back to native")
        
        elif connection_info["method"] == "individual":
            # Use individual MCP server
            try:
                tools = asyncio.run(client.get_tools())
                repo_tool = next((t for t in tools if "repository" in t.name.lower()), None)
                if repo_tool:
                    result = repo_tool.func(owner=owner, repo=repo)
                    result["connection_method"] = "individual"
                    return result
                else:
                    logger.warning("No repository tool found in MCP server, falling back to native")
            except Exception as e:
                logger.warning(f"Individual MCP server failed: {e}, falling back to native")
        
        # Native fallback
        native_tool = client._create_github_repo_tool()
        result = native_tool.func(owner=owner, repo=repo)
        return result
        
    except Exception as e:
        logger.error(f"GitHub repository lookup failed: {e}")
        return {
            "success": False,
            "error": f"Repository lookup failed: {str(e)}",
            "connection_method": "native"
        }


@tool
def github_search_repositories_hybrid(query: str, sort: str = "stars", limit: int = 10, github_token: str = None) -> Dict[str, Any]:
    """Search GitHub repositories using hybrid MCP strategy.
    
    Args:
        query: Search query
        sort: Sort order (stars, forks, updated)
        limit: Maximum number of results
        github_token: GitHub token (optional, uses env var if not provided)
    """
    try:
        if not github_token:
            github_token = get_github_token()
        
        client = GitHubMCPClient(github_token)
        connection_info = client.mcp_manager.get_connection_info("github")
        
        if connection_info["method"] == "aggregator":
            # Use aggregator
            response = requests.post(
                f"{connection_info['url']}/tools/execute", 
                json={
                    "tool": "search_repositories",
                    "arguments": {"query": query, "sort": sort, "limit": limit}
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                result["connection_method"] = "aggregator"
                return result
            else:
                logger.warning("Aggregator failed, falling back to native")
        
        elif connection_info["method"] == "individual":
            # Use individual MCP server
            try:
                tools = asyncio.run(client.get_tools())
                search_tool = next((t for t in tools if "search" in t.name.lower()), None)
                if search_tool:
                    result = search_tool.func(query=query, sort=sort, limit=limit)
                    result["connection_method"] = "individual"
                    return result
                else:
                    logger.warning("No search tool found in MCP server, falling back to native")
            except Exception as e:
                logger.warning(f"Individual MCP server failed: {e}, falling back to native")
        
        # Native fallback
        native_tool = client._create_github_search_tool()
        result = native_tool.func(query=query, sort=sort, limit=limit)
        return result
        
    except Exception as e:
        logger.error(f"GitHub search failed: {e}")
        return {
            "success": False,
            "error": f"Search failed: {str(e)}",
            "connection_method": "native"
        }


@tool
def github_list_issues_hybrid(owner: str, repo: str, state: str = "open", limit: int = 10, github_token: str = None) -> Dict[str, Any]:
    """List GitHub repository issues using hybrid MCP strategy.
    
    Args:
        owner: Repository owner/organization
        repo: Repository name
        state: Issue state (open, closed, all)
        limit: Maximum number of issues to return
        github_token: GitHub token (optional, uses env var if not provided)
    """
    try:
        if not github_token:
            github_token = get_github_token()
        
        client = GitHubMCPClient(github_token)
        connection_info = client.mcp_manager.get_connection_info("github")
        
        if connection_info["method"] == "aggregator":
            # Use aggregator
            response = requests.post(
                f"{connection_info['url']}/tools/execute",
                json={
                    "tool": "list_issues",
                    "arguments": {"owner": owner, "repo": repo, "state": state, "limit": limit}
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                result["connection_method"] = "aggregator"
                return result
            else:
                logger.warning("Aggregator failed, falling back to native")
        
        elif connection_info["method"] == "individual":
            # Use individual MCP server
            try:
                tools = asyncio.run(client.get_tools())
                issues_tool = next((t for t in tools if "issue" in t.name.lower()), None)
                if issues_tool:
                    result = issues_tool.func(owner=owner, repo=repo, state=state, limit=limit)
                    result["connection_method"] = "individual"
                    return result
                else:
                    logger.warning("No issues tool found in MCP server, falling back to native")
            except Exception as e:
                logger.warning(f"Individual MCP server failed: {e}, falling back to native")
        
        # Native fallback
        native_tool = client._create_github_issue_tool()
        result = native_tool.func(owner=owner, repo=repo, state=state, limit=limit)
        return result
        
    except Exception as e:
        logger.error(f"GitHub issues lookup failed: {e}")
        return {
            "success": False,
            "error": f"Issues lookup failed: {str(e)}",
            "connection_method": "native"
        }


@tool 
def github_get_file_content_hybrid(owner: str, repo: str, path: str, ref: str = "main", github_token: str = None) -> Dict[str, Any]:
    """Get file content from GitHub repository using hybrid MCP strategy.
    
    Args:
        owner: Repository owner/organization
        repo: Repository name
        path: File path in repository
        ref: Branch/commit reference (default: main)
        github_token: GitHub token (optional, uses env var if not provided)
    """
    try:
        if not github_token:
            github_token = get_github_token()
        
        client = GitHubMCPClient(github_token)
        connection_info = client.mcp_manager.get_connection_info("github")
        
        if connection_info["method"] == "aggregator":
            # Use aggregator
            response = requests.post(
                f"{connection_info['url']}/tools/execute",
                json={
                    "tool": "get_file_content",
                    "arguments": {"owner": owner, "repo": repo, "path": path, "ref": ref}
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                result["connection_method"] = "aggregator"
                return result
            else:
                logger.warning("Aggregator failed, falling back to native")
        
        elif connection_info["method"] == "individual":
            # Use individual MCP server
            try:
                tools = asyncio.run(client.get_tools())
                file_tool = next((t for t in tools if "file" in t.name.lower() or "content" in t.name.lower()), None)
                if file_tool:
                    result = file_tool.func(owner=owner, repo=repo, path=path, ref=ref)
                    result["connection_method"] = "individual"
                    return result
                else:
                    logger.warning("No file tool found in MCP server, falling back to native")
            except Exception as e:
                logger.warning(f"Individual MCP server failed: {e}, falling back to native")
        
        # Native fallback
        native_tool = client._create_github_file_tool()
        result = native_tool.func(owner=owner, repo=repo, path=path, ref=ref)
        return result
        
    except Exception as e:
        logger.error(f"GitHub file lookup failed: {e}")
        return {
            "success": False,
            "error": f"File lookup failed: {str(e)}",
            "connection_method": "native"
        }


async def create_github_mcp_tools(
    github_token: str, 
    server_path: str = None,
    toolsets: Optional[List[str]] = None
) -> List[Tool]:
    """
    Create GitHub MCP tools for use in LangGraph agents using hybrid connection strategy.
    
    Args:
        github_token: GitHub Personal Access Token
        server_path: Path to the github-mcp-server executable
        toolsets: List of toolsets to enable
        
    Returns:
        List of LangChain tools from GitHub MCP server (with hybrid fallback)
    """
    client = GitHubMCPClient(github_token, server_path, toolsets)
    tools = await client.get_tools()
    
    # Add connection method info to each tool result
    for tool in tools:
        original_func = tool.func
        
        def enhanced_func(*args, **kwargs):
            result = original_func(*args, **kwargs)
            if isinstance(result, dict):
                if "connection_method" not in result:
                    result["connection_method"] = getattr(client, '_connection_method', 'unknown')
            return result
        
        tool.func = enhanced_func
    
    return tools


async def create_github_repository_tools(
    github_token: str,
    server_path: str = None
) -> List[Tool]:
    """
    Create GitHub repository management tools specifically using hybrid strategy.
    
    Args:
        github_token: GitHub Personal Access Token
        server_path: Path to the github-mcp-server executable
        
    Returns:
        List of repository-related LangChain tools (with hybrid fallback)
    """
    client = GitHubMCPClient(
        github_token=github_token,
        server_path=server_path,
        toolsets=["repos", "context"]  # Focus on repository operations
    )
    return await client.get_repository_tools()


# Convenience function for getting GitHub token from environment
def get_github_token() -> str:
    """Get GitHub token from environment variables."""
    token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError(
            "GitHub token not found. Please set GITHUB_PERSONAL_ACCESS_TOKEN "
            "or GITHUB_TOKEN environment variable."
        )
    return token


# Hybrid tool validation function
@tool
def validate_github_mcp_connection() -> Dict[str, Any]:
    """Validate GitHub MCP connection using hybrid strategy."""
    try:
        connection_info = _mcp_github_manager.get_connection_info("github")
        
        validation_results = {
            "connection_method": connection_info["method"],
            "available": connection_info["available"],
            "aggregator_health": _mcp_github_manager.check_aggregator_health(),
            "individual_server_available": _mcp_github_manager._check_command_exists("github-mcp-server"),
            "native_fallback": True,  # Always available
            "github_token_configured": bool(os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN"))
        }
        
        return {
            "success": True,
            "connection_method": connection_info["method"],
            "validation_results": validation_results,
            "recommended_setup": {
                "aggregator": "Install MCP aggregator like MCPX or mcgravity",
                "individual_server": "Install github-mcp-server binary",
                "native": "No additional setup required - uses GitHub REST API"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Validation failed: {str(e)}",
            "connection_method": "unknown"
        }


# Example usage function with hybrid strategy validation
async def test_github_mcp():
    """Test function to verify GitHub MCP integration with hybrid strategy."""
    try:
        # First validate the connection
        validation = validate_github_mcp_connection()
        print("=== GitHub MCP Hybrid Connection Validation ===")
        print(f"Connection Method: {validation.get('validation_results', {}).get('connection_method', 'unknown')}")
        print(f"Available: {validation.get('validation_results', {}).get('available', False)}")
        print(f"Aggregator Health: {validation.get('validation_results', {}).get('aggregator_health', False)}")
        print(f"Individual Server Available: {validation.get('validation_results', {}).get('individual_server_available', False)}")
        print(f"Native Fallback: {validation.get('validation_results', {}).get('native_fallback', False)}")
        print(f"GitHub Token Configured: {validation.get('validation_results', {}).get('github_token_configured', False)}")
        
        if not validation.get('validation_results', {}).get('github_token_configured', False):
            print("\nWarning: No GitHub token configured. Some operations may be rate-limited.")
            print("Set GITHUB_PERSONAL_ACCESS_TOKEN or GITHUB_TOKEN environment variable.")
            return
        
        print("\n=== Testing GitHub Tools ===")
        
        token = get_github_token()
        tools = await create_github_mcp_tools(token)
        
        print(f"Successfully loaded {len(tools)} GitHub MCP tools:")
        for tool in tools[:10]:  # Show first 10 tools
            print(f"  - {tool.name}: {tool.description}")
        
        if len(tools) > 10:
            print(f"  ... and {len(tools) - 10} more tools")
        
        # Test a hybrid tool
        print("\n=== Testing Hybrid Tool ===")
        test_result = github_get_repository_info.func(owner="microsoft", repo="vscode")
        print(f"Repository lookup via {test_result.get('connection_method', 'unknown')}: {test_result.get('success', False)}")
        
        if test_result.get("success"):
            repo_info = test_result.get("repository", {})
            print(f"  Repository: {repo_info.get('full_name', 'N/A')}")
            print(f"  Stars: {repo_info.get('stars', 'N/A')}")
            print(f"  Language: {repo_info.get('language', 'N/A')}")
            
    except Exception as e:
        print(f"Error testing GitHub MCP: {e}")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_github_mcp())
