"""Unit tests for GitHub tools."""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from dev_team.tools import (
    github_get_issues,
    github_get_issue,
    github_comment_on_issue,
    github_list_pull_requests,
    github_get_pull_request,
    github_create_pull_request,
    github_create_file,
    github_read_file,
    github_update_file,
    github_delete_file,
    github_list_branches,
    github_create_branch,
    github_set_active_branch,
    github_search_code,
    github_search_issues,
    github_get_directory_contents,
    github_get_latest_release,
    github_create_repository,
    _get_github_toolkit,
)


class TestGitHubToolkitHelper:
    """Test suite for GitHub toolkit helper function."""

    @patch('dev_team.tools.GitHubAPIWrapper')
    @patch('dev_team.tools.GitHubToolkit')
    def test_get_github_toolkit_default_repo(self, mock_toolkit_class, mock_wrapper_class):
        """Test getting GitHub toolkit with default repository."""
        mock_wrapper = Mock()
        mock_wrapper_class.return_value = mock_wrapper
        
        mock_toolkit = Mock()
        mock_toolkit_class.from_github_api_wrapper.return_value = mock_toolkit
        
        result = _get_github_toolkit()
        
        assert result == mock_toolkit
        mock_wrapper_class.assert_called_once()
        mock_toolkit_class.from_github_api_wrapper.assert_called_once_with(
            mock_wrapper, include_release_tools=True
        )

    @patch('dev_team.tools.GitHubAPIWrapper')
    @patch('dev_team.tools.GitHubToolkit')
    def test_get_github_toolkit_custom_repo(self, mock_toolkit_class, mock_wrapper_class):
        """Test getting GitHub toolkit with custom repository."""
        mock_wrapper = Mock()
        mock_wrapper_class.return_value = mock_wrapper
        
        mock_toolkit = Mock()
        mock_toolkit_class.from_github_api_wrapper.return_value = mock_toolkit
        
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": "original/repo"}):
            result = _get_github_toolkit("custom/repo")
            
            assert result == mock_toolkit
            # Should temporarily change the repo
            mock_wrapper_class.assert_called_once()

    @patch('dev_team.tools.GitHubAPIWrapper')
    def test_get_github_toolkit_error_handling(self, mock_wrapper_class):
        """Test GitHub toolkit error handling."""
        mock_wrapper_class.side_effect = Exception("API error")
        
        result = _get_github_toolkit()
        
        assert result is None


class TestGitHubIssueTools:
    """Test suite for GitHub issue management tools."""

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_get_issues_success(self, mock_get_toolkit):
        """Test successful GitHub issues retrieval."""
        mock_tool = Mock()
        mock_tool.name = "Get Issues"
        mock_tool.invoke.return_value = "Issue list data"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        result = github_get_issues.invoke({
            "repository": "test/repo",
            "state": "open",
            "limit": 5
        })
        
        assert "📋 **GitHub Issues**" in result
        assert "test/repo" in result
        assert "Issue list data" in result
        mock_tool.invoke.assert_called_once_with({})

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_get_issues_no_toolkit(self, mock_get_toolkit):
        """Test GitHub issues when toolkit fails."""
        mock_get_toolkit.return_value = None
        
        result = github_get_issues.invoke({})
        
        assert "❌ Failed to initialize GitHub connection" in result

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_get_issue_success(self, mock_get_toolkit):
        """Test successful GitHub issue retrieval."""
        mock_tool = Mock()
        mock_tool.name = "Get Issue"
        mock_tool.invoke.return_value = "Issue #123 details"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        result = github_get_issue.invoke({
            "issue_number": 123,
            "repository": "test/repo"
        })
        
        assert "🔍 **GitHub Issue #123**" in result
        assert "Issue #123 details" in result
        mock_tool.invoke.assert_called_once_with({"issue_number": 123})

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_comment_on_issue_success(self, mock_get_toolkit):
        """Test successful GitHub issue commenting."""
        mock_tool = Mock()
        mock_tool.name = "Comment on Issue"
        mock_tool.invoke.return_value = "Comment posted successfully"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        result = github_comment_on_issue.invoke({
            "issue_number": 123,
            "comment": "Test comment",
            "repository": "test/repo"
        })
        
        assert "💬 **Comment Posted** on Issue #123" in result
        assert "Comment posted successfully" in result
        mock_tool.invoke.assert_called_once_with({
            "issue_number": 123,
            "comment": "Test comment"
        })


class TestGitHubPullRequestTools:
    """Test suite for GitHub pull request tools."""

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_list_pull_requests_success(self, mock_get_toolkit):
        """Test successful GitHub PR listing."""
        mock_tool = Mock()
        mock_tool.name = "List open pull requests (PRs)"
        mock_tool.invoke.return_value = "PR list data"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        result = github_list_pull_requests.invoke({
            "repository": "test/repo",
            "state": "open"
        })
        
        assert "🔄 **GitHub Pull Requests**" in result
        assert "PR list data" in result

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_get_pull_request_success(self, mock_get_toolkit):
        """Test successful GitHub PR retrieval."""
        mock_tool = Mock()
        mock_tool.name = "Get Pull Request"
        mock_tool.invoke.return_value = "PR #456 details"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        result = github_get_pull_request.invoke({
            "pr_number": 456,
            "repository": "test/repo"
        })
        
        assert "🔄 **GitHub Pull Request #456**" in result
        assert "PR #456 details" in result
        mock_tool.invoke.assert_called_once_with({"pr_number": 456})

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_create_pull_request_success(self, mock_get_toolkit):
        """Test successful GitHub PR creation."""
        mock_tool = Mock()
        mock_tool.name = "Create Pull Request"
        mock_tool.invoke.return_value = "PR created successfully"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        result = github_create_pull_request.invoke({
            "title": "Test PR",
            "body": "Test PR description",
            "head_branch": "feature",
            "base_branch": "main"
        })
        
        assert "✨ **GitHub Pull Request Created**" in result
        assert "PR created successfully" in result
        mock_tool.invoke.assert_called_once_with({
            "title": "Test PR",
            "body": "Test PR description",
            "head": "feature",
            "base": "main"
        })


class TestGitHubFileTools:
    """Test suite for GitHub file management tools."""

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_create_file_success(self, mock_get_toolkit):
        """Test successful GitHub file creation."""
        mock_tool = Mock()
        mock_tool.name = "Create File"
        mock_tool.invoke.return_value = "File created successfully"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        result = github_create_file.invoke({
            "file_path": "test.txt",
            "content": "Test content",
            "commit_message": "Add test file"
        })
        
        assert "📄 **GitHub File Created**" in result
        assert "test.txt" in result
        assert "File created successfully" in result
        mock_tool.invoke.assert_called_once_with({
            "file_path": "test.txt",
            "file_contents": "Test content",
            "commit_message": "Add test file"
        })

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_read_file_success(self, mock_get_toolkit):
        """Test successful GitHub file reading."""
        mock_tool = Mock()
        mock_tool.name = "Read File"
        mock_tool.invoke.return_value = "File content data"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        result = github_read_file.invoke({
            "file_path": "test.txt",
            "repository": "test/repo"
        })
        
        assert "📖 **GitHub File Content**" in result
        assert "test.txt" in result
        assert "File content data" in result
        mock_tool.invoke.assert_called_once_with({"file_path": "test.txt"})

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_update_file_success(self, mock_get_toolkit):
        """Test successful GitHub file update."""
        mock_tool = Mock()
        mock_tool.name = "Update File"
        mock_tool.invoke.return_value = "File updated successfully"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        result = github_update_file.invoke({
            "file_path": "test.txt",
            "content": "Updated content",
            "commit_message": "Update test file"
        })
        
        assert "✏️ **GitHub File Updated**" in result
        assert "File updated successfully" in result
        mock_tool.invoke.assert_called_once_with({
            "file_path": "test.txt",
            "file_contents": "Updated content",
            "commit_message": "Update test file"
        })

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_delete_file_success(self, mock_get_toolkit):
        """Test successful GitHub file deletion."""
        mock_tool = Mock()
        mock_tool.name = "Delete File"
        mock_tool.invoke.return_value = "File deleted successfully"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        result = github_delete_file.invoke({
            "file_path": "test.txt",
            "commit_message": "Delete test file"
        })
        
        assert "🗑️ **GitHub File Deleted**" in result
        assert "File deleted successfully" in result
        mock_tool.invoke.assert_called_once_with({
            "file_path": "test.txt",
            "commit_message": "Delete test file"
        })


class TestGitHubBranchTools:
    """Test suite for GitHub branch management tools."""

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_list_branches_success(self, mock_get_toolkit):
        """Test successful GitHub branch listing."""
        mock_tool = Mock()
        mock_tool.name = "List branches in this repository"
        mock_tool.invoke.return_value = "Branch list data"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        result = github_list_branches.invoke({
            "repository": "test/repo"
        })
        
        assert "🌿 **GitHub Branches**" in result
        assert "Branch list data" in result

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_create_branch_success(self, mock_get_toolkit):
        """Test successful GitHub branch creation."""
        mock_tool = Mock()
        mock_tool.name = "Create a new branch"
        mock_tool.invoke.return_value = "Branch created successfully"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        result = github_create_branch.invoke({
            "branch_name": "feature-branch",
            "repository": "test/repo"
        })
        
        assert "🌱 **GitHub Branch Created**" in result
        assert "feature-branch" in result
        assert "Branch created successfully" in result
        mock_tool.invoke.assert_called_once_with({"branch_name": "feature-branch"})

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_set_active_branch_success(self, mock_get_toolkit):
        """Test successful GitHub active branch setting."""
        mock_tool = Mock()
        mock_tool.name = "Set active branch"
        mock_tool.invoke.return_value = "Active branch set successfully"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        result = github_set_active_branch.invoke({
            "branch_name": "main",
            "repository": "test/repo"
        })
        
        assert "🎯 **GitHub Active Branch Set**" in result
        assert "main" in result
        assert "Active branch set successfully" in result
        mock_tool.invoke.assert_called_once_with({"branch_name": "main"})


class TestGitHubSearchTools:
    """Test suite for GitHub search tools."""

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_search_code_success(self, mock_get_toolkit):
        """Test successful GitHub code search."""
        mock_tool = Mock()
        mock_tool.name = "Search code"
        mock_tool.invoke.return_value = "Code search results"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        result = github_search_code.invoke({
            "query": "function test",
            "repository": "test/repo",
            "language": "python"
        })
        
        assert "🔍 **GitHub Code Search**" in result
        assert "function test" in result
        assert "Code search results" in result
        mock_tool.invoke.assert_called_once_with({"query": "function test language:python"})

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_search_issues_success(self, mock_get_toolkit):
        """Test successful GitHub issues search."""
        mock_tool = Mock()
        mock_tool.name = "Search issues and pull requests"
        mock_tool.invoke.return_value = "Issue search results"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        result = github_search_issues.invoke({
            "query": "bug report",
            "repository": "test/repo",
            "state": "open"
        })
        
        assert "🔍 **GitHub Issues Search**" in result
        assert "bug report" in result
        assert "Issue search results" in result
        mock_tool.invoke.assert_called_once_with({"query": "bug report state:open"})


class TestGitHubDirectoryTools:
    """Test suite for GitHub directory tools."""

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_get_directory_contents_success(self, mock_get_toolkit):
        """Test successful GitHub directory contents retrieval."""
        mock_tool = Mock()
        mock_tool.name = "Get files from a directory"
        mock_tool.invoke.return_value = "Directory contents data"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        result = github_get_directory_contents.invoke({
            "directory_path": "src",
            "repository": "test/repo"
        })
        
        assert "📁 **GitHub Directory Contents**" in result
        assert "src" in result
        assert "Directory contents data" in result
        mock_tool.invoke.assert_called_once_with({"directory_path": "src"})

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_get_directory_contents_root(self, mock_get_toolkit):
        """Test GitHub directory contents for root directory."""
        mock_tool = Mock()
        mock_tool.name = "Get files from a directory"
        mock_tool.invoke.return_value = "Root directory contents"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        result = github_get_directory_contents.invoke({
            "directory_path": "",
            "repository": "test/repo"
        })
        
        assert "root" in result
        mock_tool.invoke.assert_called_once_with({"directory_path": ""})


class TestGitHubReleaseTools:
    """Test suite for GitHub release tools."""

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_get_latest_release_success(self, mock_get_toolkit):
        """Test successful GitHub latest release retrieval."""
        mock_tool = Mock()
        mock_tool.name = "Get Latest Release"
        mock_tool.invoke.return_value = "Latest release data"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        result = github_get_latest_release.invoke({
            "repository": "test/repo"
        })
        
        assert "🚀 **GitHub Latest Release**" in result
        assert "Latest release data" in result
        mock_tool.invoke.assert_called_once_with({})


class TestGitHubRepositoryTools:
    """Test suite for GitHub repository creation tools."""

    @patch('github.Github')  # Patch the actual Github class from github module
    def test_github_create_repository_success(self, mock_github_class):
        """Test successful GitHub repository creation."""
        mock_repo = Mock()
        mock_repo.full_name = "LimbicNode42/test-repo"
        mock_repo.html_url = "https://github.com/LimbicNode42/test-repo"
        mock_repo.clone_url = "https://github.com/LimbicNode42/test-repo.git"
        
        mock_user = Mock()
        mock_user.create_repo.return_value = mock_repo
        
        mock_github = Mock()
        mock_github.get_user.return_value = mock_user
        mock_github_class.return_value = mock_github
        
        with patch.dict(os.environ, {
            "GITHUB_APP_PRIVATE_KEY": "test_token",
            "GITHUB_APP_ID": "123456"
        }):
            result = github_create_repository.invoke({
                "name": "test-repo",
                "description": "Test repository",
                "private": False
            })
        
        assert "✨ **GitHub Repository Created**" in result
        assert "LimbicNode42/test-repo" in result
        assert "Test repository" in result
        mock_user.create_repo.assert_called_once_with(
            name="test-repo",
            description="Test repository",
            private=False,
            auto_init=True
        )

    def test_github_create_repository_missing_auth(self):
        """Test GitHub repository creation with missing authentication."""
        with patch.dict(os.environ, {}, clear=True):
            result = github_create_repository.invoke({
                "name": "test-repo",
                "description": "Test repository"
            })
        
        assert "❌ GitHub authentication not configured" in result


class TestGitHubErrorHandling:
    """Test suite for GitHub tools error handling."""

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_tool_not_found(self, mock_get_toolkit):
        """Test behavior when specific GitHub tool is not found."""
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = []  # No tools available
        mock_get_toolkit.return_value = mock_toolkit
        
        result = github_get_issues.invoke({})
        
        assert "❌ Issues tool not found" in result

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_tool_execution_error(self, mock_get_toolkit):
        """Test GitHub tool execution error handling."""
        mock_tool = Mock()
        mock_tool.name = "Get Issues"
        mock_tool.invoke.side_effect = Exception("API rate limit exceeded")
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        result = github_get_issues.invoke({})
        
        assert "❌ Error fetching GitHub issues" in result
        assert "API rate limit exceeded" in result

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_multiple_tools_with_similar_names(self, mock_get_toolkit):
        """Test GitHub tool selection with multiple similar tools."""
        mock_tool1 = Mock()
        mock_tool1.name = "Get Issues Advanced"
        
        mock_tool2 = Mock()
        mock_tool2.name = "Get Issues"
        mock_tool2.invoke.return_value = "Correct tool result"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool1, mock_tool2]
        mock_get_toolkit.return_value = mock_toolkit
        
        result = github_get_issues.invoke({})
        
        # Should select the exact match
        assert "Correct tool result" in result
        mock_tool2.invoke.assert_called_once()
        mock_tool1.invoke.assert_not_called()


class TestGitHubParameterHandling:
    """Test suite for GitHub tools parameter handling."""

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_optional_parameters(self, mock_get_toolkit):
        """Test GitHub tools with optional parameters."""
        mock_tool = Mock()
        mock_tool.name = "Create Pull Request"
        mock_tool.invoke.return_value = "PR created"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        result = github_create_pull_request.invoke({
            "title": "Test PR",
            "body": "Test description"
            # No head_branch or base_branch specified
        })
        
        assert "✨ **GitHub Pull Request Created**" in result
        mock_tool.invoke.assert_called_once_with({
            "title": "Test PR",
            "body": "Test description"
        })

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_search_without_filters(self, mock_get_toolkit):
        """Test GitHub search without optional filters."""
        mock_tool = Mock()
        mock_tool.name = "Search code"
        mock_tool.invoke.return_value = "Search results"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        result = github_search_code.invoke({
            "query": "test function"
            # No language filter
        })
        
        assert "Search results" in result
        mock_tool.invoke.assert_called_once_with({"query": "test function"})
