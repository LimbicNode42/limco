"""GitHub integration tools using MCP (Model Context Protocol)."""

import asyncio
import concurrent.futures

# Direct import from github_mcp module (now in same directory)
try:
    from .github_mcp import GitHubMCPClient, create_github_mcp_tools, get_github_token
except ImportError:
    print("Warning: GitHub MCP integration not available - github_mcp module not found")
    GitHubMCPClient = None
    create_github_mcp_tools = None
    get_github_token = None


async def get_github_mcp_tools():
    """Get GitHub MCP tools asynchronously."""
    if not create_github_mcp_tools or not get_github_token:
        print("Warning: GitHub MCP integration not available")
        return []
    
    try:
        token = get_github_token()
        # Focus on repository and issue management toolsets
        toolsets = ["repos", "issues", "pull_requests", "context"]
        tools = await create_github_mcp_tools(token, toolsets=toolsets)
        return tools
    except Exception as e:
        print(f"Warning: Failed to load GitHub MCP tools: {e}")
        return []


def get_github_mcp_tools_sync():
    """Get GitHub MCP tools synchronously (for use in get_all_tools)."""
    if not create_github_mcp_tools or not get_github_token:
        return []
        
    try:
        # Check if we're in an async context
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, use run_coroutine_threadsafe
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, get_github_mcp_tools())
                return future.result(timeout=10)
        except RuntimeError:
            # No running loop, we can use asyncio.run
            return asyncio.run(get_github_mcp_tools())
    except Exception as e:
        print(f"Warning: Failed to load GitHub MCP tools synchronously: {e}")
        return []


__all__ = [
    'get_github_mcp_tools',
    'get_github_mcp_tools_sync'
]
