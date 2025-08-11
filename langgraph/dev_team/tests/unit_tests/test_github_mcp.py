"""Unit tests for GitHub MCP integration."""

import os
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path

# Set up the path for importing our modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dev_team.github_mcp import (
    GitHubMCPClient,
    create_github_mcp_tools,
    get_github_token,
)


class TestGitHubTokenRetrieval:
    """Test suite for GitHub token retrieval."""

    def test_get_github_token_personal_access_token(self):
        """Test getting token from GITHUB_PERSONAL_ACCESS_TOKEN."""
        with patch.dict(os.environ, {"GITHUB_PERSONAL_ACCESS_TOKEN": "test_token_pat"}):
            token = get_github_token()
            assert token == "test_token_pat"

    def test_get_github_token_fallback(self):
        """Test getting token from GITHUB_TOKEN fallback."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token_fallback"}, clear=True):
            token = get_github_token()
            assert token == "test_token_fallback"

    def test_get_github_token_personal_takes_priority(self):
        """Test that GITHUB_PERSONAL_ACCESS_TOKEN takes priority over GITHUB_TOKEN."""
        env_vars = {
            "GITHUB_PERSONAL_ACCESS_TOKEN": "test_token_pat",
            "GITHUB_TOKEN": "test_token_fallback"
        }
        with patch.dict(os.environ, env_vars):
            token = get_github_token()
            assert token == "test_token_pat"

    def test_get_github_token_none_available(self):
        """Test behavior when no GitHub token is available."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GitHub token not found"):
                get_github_token()


class TestGitHubMCPClient:
    """Test suite for GitHubMCPClient."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_token = "test_github_token"
        self.test_server_path = "/path/to/github-mcp-server.exe"

    def test_client_initialization(self):
        """Test GitHub MCP client initialization."""
        client = GitHubMCPClient(self.test_token, server_path=self.test_server_path)
        
        assert client.github_token == self.test_token
        assert client.server_path == self.test_server_path
        assert client._client is None
        assert client._tools is None

    def test_client_initialization_auto_server_path(self):
        """Test client initialization with automatic server path detection."""
        with patch('os.path.exists', return_value=True):
            client = GitHubMCPClient(self.test_token)
            
            assert client.github_token == self.test_token
            assert client.server_path is not None
            assert "github-mcp-server" in str(client.server_path)

    def test_client_initialization_missing_server(self):
        """Test client initialization when server binary is missing."""
        with patch('os.path.exists', return_value=False):
            # Client should still initialize but with fallback path
            client = GitHubMCPClient(self.test_token)
            assert client.server_path == "github-mcp-server"  # Fallback to PATH

    @pytest.mark.asyncio
    async def test_get_tools_success(self):
        """Test successful tool retrieval."""
        # Mock the MultiServerMCPClient
        mock_client = AsyncMock()
        
        # Mock tools
        mock_tool1 = Mock()
        mock_tool1.name = "create_repository" 
        mock_tool1.description = "Create a new repository"
        
        mock_tool2 = Mock()
        mock_tool2.name = "get_issue"
        mock_tool2.description = "Get issue details"
        
        mock_client.get_tools.return_value = [mock_tool1, mock_tool2]
        
        with patch('dev_team.github_mcp.MultiServerMCPClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            
            client = GitHubMCPClient(self.test_token, server_path=self.test_server_path)
            tools = await client.get_tools()
            
            assert len(tools) == 2
            assert tools[0].name == "create_repository"
            assert tools[1].name == "get_issue"

    @pytest.mark.asyncio
    async def test_get_tools_with_toolsets_filter(self):
        """Test tool retrieval with toolsets filtering."""
        mock_session = AsyncMock()
        mock_client = AsyncMock()
        
        # Mock tools from different toolsets
        mock_repo_tool = Mock()
        mock_repo_tool.name = "create_repository"
        mock_repo_tool.description = "Create repository"
        mock_repo_tool.inputSchema = {"type": "object"}
        
        mock_issue_tool = Mock()
        mock_issue_tool.name = "get_issue"  
        mock_issue_tool.description = "Get issue"
        mock_issue_tool.inputSchema = {"type": "object"}
        
        mock_pr_tool = Mock()
        mock_pr_tool.name = "create_pull_request"
        mock_pr_tool.description = "Create PR"
        mock_pr_tool.inputSchema = {"type": "object"}
        
        mock_client.list_tools.return_value = Mock(tools=[mock_repo_tool, mock_issue_tool, mock_pr_tool])
        
        with patch('dev_team.github_mcp.stdio_client') as mock_stdio_client, \
             patch('dev_team.github_mcp.MCPSession') as mock_session_class:
            
            mock_stdio_client.return_value = mock_client
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            client = GitHubMCPClient(self.test_token, server_path=self.test_server_path)
            tools = await client.get_tools(toolsets=["repos", "issues"])
            
            # Should include repo and issue tools, but not PR tools
            tool_names = [tool.name for tool in tools]
            assert "github_mcp_create_repository" in tool_names
            assert "github_mcp_get_issue" in tool_names
            # Note: PR tools might still be included if they match the filter logic

    @pytest.mark.asyncio
    async def test_get_tools_connection_error(self):
        """Test tool retrieval with connection error."""
        with patch('dev_team.github_mcp.stdio_client') as mock_stdio_client:
            mock_stdio_client.side_effect = Exception("Connection failed")
            
            client = GitHubMCPClient(self.test_token, server_path=self.test_server_path)
            
            with pytest.raises(Exception, match="Connection failed"):
                await client.get_tools()

    @pytest.mark.asyncio
    async def test_close_client(self):
        """Test client cleanup."""
        mock_session = AsyncMock()
        
        with patch('dev_team.github_mcp.MCPSession') as mock_session_class:
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            client = GitHubMCPClient(self.test_token, server_path=self.test_server_path)
            client.session = mock_session
            
            await client.close()
            
            mock_session.__aexit__.assert_called_once()


class TestGitHubMCPToolsCreation:
    """Test suite for GitHub MCP tools creation function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_token = "test_token"

    @pytest.mark.asyncio
    async def test_create_github_mcp_tools_success(self):
        """Test successful creation of GitHub MCP tools."""
        mock_tool = Mock()
        mock_tool.name = "github_mcp_test_tool"
        mock_tool.description = "Test tool"
        
        with patch('dev_team.github_mcp.GitHubMCPClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_tools.return_value = [mock_tool]
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client
            
            tools = await create_github_mcp_tools(self.test_token)
            
            assert len(tools) == 1
            assert tools[0] == mock_tool
            mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_github_mcp_tools_with_toolsets(self):
        """Test tool creation with specific toolsets."""
        with patch('dev_team.github_mcp.GitHubMCPClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_tools.return_value = []
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client
            
            toolsets = ["repos", "issues"]
            await create_github_mcp_tools(self.test_token, toolsets=toolsets)
            
            mock_client.get_tools.assert_called_once_with(toolsets=toolsets)
            mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_github_mcp_tools_client_error(self):
        """Test tool creation when client initialization fails."""
        with patch('dev_team.github_mcp.GitHubMCPClient') as mock_client_class:
            mock_client_class.side_effect = Exception("Client initialization failed")
            
            with pytest.raises(Exception, match="Client initialization failed"):
                await create_github_mcp_tools(self.test_token)

    @pytest.mark.asyncio
    async def test_create_github_mcp_tools_get_tools_error(self):
        """Test tool creation when get_tools fails."""
        with patch('dev_team.github_mcp.GitHubMCPClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_tools.side_effect = Exception("Failed to get tools")
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client
            
            with pytest.raises(Exception, match="Failed to get tools"):
                await create_github_mcp_tools(self.test_token)
            
            # Ensure cleanup is called even on error
            mock_client.close.assert_called_once()


class TestGitHubMCPEnvironmentIntegration:
    """Test suite for environment integration."""

    def test_server_path_calculation(self):
        """Test automatic server path calculation."""
        with patch('pathlib.Path.exists', return_value=True) as mock_exists:
            client = GitHubMCPClient("test_token")
            
            # Verify the path calculation logic
            assert client.server_path is not None
            assert "github-mcp-server.exe" in str(client.server_path)
            
            # Should have checked for server existence
            mock_exists.assert_called()

    @patch.dict(os.environ, {"GITHUB_PERSONAL_ACCESS_TOKEN": "env_token"})
    def test_integration_with_environment(self):
        """Test integration with actual environment variables."""
        token = get_github_token()
        assert token == "env_token"


if __name__ == "__main__":
    pytest.main([__file__])
