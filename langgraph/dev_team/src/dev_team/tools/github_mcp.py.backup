"""GitHub MCP Server Integration for LangGraph agents."""

import os
import asyncio
from typing import List, Optional
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import Tool
import logging

logger = logging.getLogger(__name__)

class GitHubMCPClient:
    """Client for GitHub MCP Server integration."""
    
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
        """Initialize the MCP client if not already done."""
        if self._client is None:
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
            
            logger.info(f"Initialized GitHub MCP client with toolsets: {self.toolsets}")
    
    async def get_tools(self) -> List[Tool]:
        """Get all available GitHub tools from the MCP server."""
        if self._tools is None:
            await self._initialize_client()
            
            try:
                self._tools = await self._client.get_tools()
                logger.info(f"Retrieved {len(self._tools)} GitHub MCP tools")
                
                # Log available tools for debugging
                tool_names = [tool.name for tool in self._tools]
                logger.debug(f"Available GitHub MCP tools: {tool_names}")
                
            except Exception as e:
                logger.error(f"Failed to get GitHub MCP tools: {e}")
                raise
        
        return self._tools
    
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


async def create_github_mcp_tools(
    github_token: str, 
    server_path: str = None,
    toolsets: Optional[List[str]] = None
) -> List[Tool]:
    """
    Create GitHub MCP tools for use in LangGraph agents.
    
    Args:
        github_token: GitHub Personal Access Token
        server_path: Path to the github-mcp-server executable
        toolsets: List of toolsets to enable
        
    Returns:
        List of LangChain tools from GitHub MCP server
    """
    client = GitHubMCPClient(github_token, server_path, toolsets)
    return await client.get_tools()


async def create_github_repository_tools(
    github_token: str,
    server_path: str = None
) -> List[Tool]:
    """
    Create GitHub repository management tools specifically.
    
    Args:
        github_token: GitHub Personal Access Token
        server_path: Path to the github-mcp-server executable
        
    Returns:
        List of repository-related LangChain tools
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


# Example usage function
async def test_github_mcp():
    """Test function to verify GitHub MCP integration."""
    try:
        token = get_github_token()
        tools = await create_github_mcp_tools(token)
        
        print(f"Successfully loaded {len(tools)} GitHub MCP tools:")
        for tool in tools[:10]:  # Show first 10 tools
            print(f"  - {tool.name}: {tool.description}")
        
        if len(tools) > 10:
            print(f"  ... and {len(tools) - 10} more tools")
            
    except Exception as e:
        print(f"Error testing GitHub MCP: {e}")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_github_mcp())
