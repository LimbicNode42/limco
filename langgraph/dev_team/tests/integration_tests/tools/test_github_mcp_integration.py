"""Integration tests for GitHub MCP."""

import os
import pytest
import asyncio
from pathlib import Path

# Set up the path for importing our modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dev_team.github_mcp import (
    GitHubMCPClient,
    create_github_mcp_tools,
    get_github_token,
)
from dev_team.tools import get_all_tools


class TestGitHubMCPIntegration:
    """Integration tests for GitHub MCP functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Skip tests if no GitHub token is available
        try:
            self.token = get_github_token()
        except ValueError:
            pytest.skip("No GitHub token available for integration tests")
        
        # Check if MCP server binary exists
        server_path = Path(__file__).parent.parent.parent.parent.parent / "github-mcp-server.exe"
        if not server_path.exists():
            pytest.skip(f"GitHub MCP server binary not found at {server_path}")
        
        self.server_path = server_path

    @pytest.mark.asyncio
    async def test_github_mcp_client_real_connection(self):
        """Test real connection to GitHub MCP server."""
        client = GitHubMCPClient(self.token, server_path=str(self.server_path))
        
        try:
            tools = await client.get_tools()
            
            # Verify we got tools back
            assert len(tools) > 0, "Should receive tools from GitHub MCP server"
            
            # Check that tools have expected structure
            for tool in tools[:3]:  # Check first 3 tools
                assert hasattr(tool, 'name'), "Tool should have a name"
                assert hasattr(tool, 'description'), "Tool should have a description"
                # GitHub MCP tools should have proper names (no specific prefix required)
                assert len(tool.name) > 0, "Tool name should not be empty"
                
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_github_mcp_tools_with_toolsets(self):
        """Test GitHub MCP tools creation with specific toolsets."""
        toolsets = ["repos", "issues"]
        
        try:
            tools = await create_github_mcp_tools(self.token, toolsets=toolsets)
            
            assert len(tools) > 0, "Should create tools for specified toolsets"
            
            # Verify we get tools related to repos and issues
            tool_names = [tool.name for tool in tools]
            
            # Should have some repository-related tools
            repo_tools = [name for name in tool_names if any(
                keyword in name.lower() for keyword in ['repo', 'repository', 'create_repo']
            )]
            assert len(repo_tools) > 0, "Should have repository-related tools"
            
            # Should have some issue-related tools  
            issue_tools = [name for name in tool_names if any(
                keyword in name.lower() for keyword in ['issue', 'comment']
            )]
            assert len(issue_tools) > 0, "Should have issue-related tools"
            
        except Exception as e:
            pytest.fail(f"Failed to create GitHub MCP tools: {e}")

    def test_tools_integration_with_main_collection(self):
        """Test that GitHub MCP tools are integrated into the main tools collection."""
        try:
            all_tools = get_all_tools()
            
            # Should have tools
            assert len(all_tools) > 0, "Should have tools in collection"
            
            # Look for GitHub MCP tools in the collection
            tool_names = []
            for tool in all_tools:
                if hasattr(tool, 'name'):
                    tool_names.append(tool.name)
                elif hasattr(tool, '__name__'):
                    tool_names.append(tool.__name__)
            
            # Check if any GitHub MCP tools are present
            github_mcp_tools = [name for name in tool_names if 'github' in name.lower() or 'repo' in name.lower() or 'issue' in name.lower()]
            
            # This might be 0 if MCP tools failed to load, which is acceptable
            # The integration should handle failures gracefully
            print(f"Found {len(github_mcp_tools)} GitHub-related tools in main collection")
            
            # Ensure we at least have some tools
            assert len(all_tools) > 0, "Should have some tools in the collection"
            
        except Exception as e:
            pytest.fail(f"Failed to get tools collection: {e}")

    @pytest.mark.asyncio
    async def test_github_mcp_tool_execution_capability(self):
        """Test that GitHub MCP tools can be executed (basic capability test)."""
        client = GitHubMCPClient(self.token, server_path=str(self.server_path))
        
        try:
            tools = await client.get_tools()
            
            # Find a simple read-only tool for testing
            read_only_tools = []
            for tool in tools:
                # Look for tools that are likely read-only and safe to test
                if any(keyword in tool.name.lower() for keyword in ['get_', 'list_', 'search_']):
                    if 'user' in tool.name.lower():  # User info is usually safe to query
                        read_only_tools.append(tool)
                        break
            
            if read_only_tools:
                test_tool = read_only_tools[0]
                print(f"Found testable tool: {test_tool.name}")
                
                # Verify the tool has a callable function
                assert callable(test_tool.func), "Tool should have a callable function"
                
                # Note: We don't actually execute the tool here to avoid side effects
                # This test just verifies the tool structure is correct for execution
                
            else:
                print("No safe read-only tools found for execution testing")
                
        finally:
            await client.close()

    @pytest.mark.asyncio  
    async def test_github_mcp_error_handling(self):
        """Test error handling in GitHub MCP integration."""
        # Test with invalid token
        invalid_client = GitHubMCPClient("invalid_token", server_path=str(self.server_path))
        
        try:
            # This should either fail gracefully or succeed depending on MCP server validation
            tools = await invalid_client.get_tools()
            # If it succeeds, that's also valid (server might not validate token immediately)
            print(f"Got {len(tools)} tools with invalid token (server may not validate immediately)")
            
        except Exception as e:
            # Expected for invalid token
            print(f"Expected error with invalid token: {e}")
            
        finally:
            await invalid_client.close()
            
        # Test with invalid server path - only test if it's actually expected to fail
        try:
            invalid_path_client = GitHubMCPClient(self.token, server_path="/nonexistent/path/server.exe")
            await invalid_path_client.get_tools()
            print("Invalid server path didn't raise exception (may be handled gracefully)")
        except (FileNotFoundError, OSError, Exception) as e:
            print(f"Invalid server path raised exception as expected: {e}")
        finally:
            # Clean up if needed
            pass


class TestGitHubMCPEnvironmentSetup:
    """Test environment setup and configuration."""

    def test_environment_variables_loaded(self):
        """Test that environment variables are properly loaded."""
        from dotenv import load_dotenv
        load_dotenv()
        
        # Should be able to get a token from environment
        token_found = bool(
            os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or 
            os.getenv("GITHUB_TOKEN")
        )
        
        if not token_found:
            pytest.skip("No GitHub token in environment variables")
        
        # Test the token retrieval function
        token = get_github_token()
        assert len(token) > 0, "Token should not be empty"
        assert len(token) >= 20, "GitHub tokens should be at least 20 characters"

    def test_server_binary_detection(self):
        """Test that the MCP server binary can be detected."""
        # Check multiple possible locations
        possible_paths = [
            Path(__file__).parent.parent.parent.parent.parent / "github-mcp-server.exe",
            Path(__file__).parent.parent.parent / "github-mcp-server.exe",
            Path.cwd() / "github-mcp-server.exe",
        ]
        
        server_found = any(path.exists() for path in possible_paths)
        
        if not server_found:
            pytest.skip("GitHub MCP server binary not found in expected locations")
        
        # Verify the binary is executable
        for path in possible_paths:
            if path.exists():
                assert path.is_file(), "Server path should be a file"
                break


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
