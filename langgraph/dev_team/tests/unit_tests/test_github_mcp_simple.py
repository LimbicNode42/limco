"""Simplified unit tests for GitHub MCP integration."""

import os
import pytest
from unittest.mock import Mock, patch, AsyncMock
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
        assert client.toolsets == ["repos", "issues", "pull_requests", "context"]

    def test_client_initialization_with_custom_toolsets(self):
        """Test client initialization with custom toolsets."""
        custom_toolsets = ["repos", "issues"]
        client = GitHubMCPClient(self.test_token, toolsets=custom_toolsets)
        
        assert client.toolsets == custom_toolsets

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
    async def test_get_tools_caching(self):
        """Test that tools are cached after first retrieval."""
        mock_client = AsyncMock()
        mock_tools = [Mock(name="tool1"), Mock(name="tool2")]
        mock_client.get_tools.return_value = mock_tools
        
        with patch('dev_team.github_mcp.MultiServerMCPClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            
            client = GitHubMCPClient(self.test_token, server_path=self.test_server_path)
            
            # First call should initialize and get tools
            tools1 = await client.get_tools()
            assert len(tools1) == 2
            
            # Second call should use cached tools
            tools2 = await client.get_tools()
            assert tools1 is tools2  # Same object reference
            
            # MultiServerMCPClient should only be created once
            mock_client_class.assert_called_once()


class TestGitHubMCPToolsCreation:
    """Test suite for GitHub MCP tools creation function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_token = "test_token"

    @pytest.mark.asyncio
    async def test_create_github_mcp_tools_success(self):
        """Test successful creation of GitHub MCP tools."""
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test tool"
        
        with patch('dev_team.github_mcp.GitHubMCPClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_tools.return_value = [mock_tool]
            mock_client_class.return_value = mock_client
            
            tools = await create_github_mcp_tools(self.test_token)
            
            assert len(tools) == 1
            assert tools[0] == mock_tool

    @pytest.mark.asyncio
    async def test_create_github_mcp_tools_with_toolsets(self):
        """Test tool creation with specific toolsets."""
        with patch('dev_team.github_mcp.GitHubMCPClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_tools.return_value = []
            mock_client_class.return_value = mock_client
            
            toolsets = ["repos", "issues"]
            await create_github_mcp_tools(self.test_token, toolsets=toolsets)
            
            # Verify client was created with correct toolsets
            mock_client_class.assert_called_once()
            args, kwargs = mock_client_class.call_args
            assert kwargs.get('toolsets') == toolsets or args[2] == toolsets

    @pytest.mark.asyncio
    async def test_create_github_mcp_tools_client_error(self):
        """Test tool creation when client initialization fails."""
        with patch('dev_team.github_mcp.GitHubMCPClient') as mock_client_class:
            mock_client_class.side_effect = Exception("Client initialization failed")
            
            with pytest.raises(Exception, match="Client initialization failed"):
                await create_github_mcp_tools(self.test_token)


class TestServerPathCalculation:
    """Test suite for server path calculation logic."""

    def test_server_path_calculation_found(self):
        """Test server path calculation when binary is found."""
        with patch('os.path.exists', return_value=True):
            client = GitHubMCPClient("test_token")
            
            # Should find the binary
            assert client.server_path is not None
            assert os.path.isabs(client.server_path)
            assert "github-mcp-server.exe" in client.server_path

    def test_server_path_calculation_not_found(self):
        """Test server path calculation when binary is not found."""
        with patch('os.path.exists', return_value=False):
            client = GitHubMCPClient("test_token")
            
            # Should fallback to PATH
            assert client.server_path == "github-mcp-server"


class TestEnvironmentIntegration:
    """Test suite for environment integration."""

    @patch.dict(os.environ, {"GITHUB_PERSONAL_ACCESS_TOKEN": "env_token"})
    def test_integration_with_environment(self):
        """Test integration with actual environment variables."""
        token = get_github_token()
        assert token == "env_token"

    def test_toolsets_environment_handling(self):
        """Test that toolsets are properly configured."""
        client = GitHubMCPClient("test_token", toolsets=["repos"])
        assert client.toolsets == ["repos"]
        
        # Default toolsets
        client_default = GitHubMCPClient("test_token")
        assert "repos" in client_default.toolsets
        assert "issues" in client_default.toolsets


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
