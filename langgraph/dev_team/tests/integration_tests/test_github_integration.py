"""Integration tests for GitHub tools in agent workflows."""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from dev_team.tools import (
    github_get_issues,
    github_create_pull_request,
    github_create_file,
    github_search_code,
    github_create_repository,
)


class TestGitHubIntegration:
    """Integration tests for GitHub tools within agent workflows."""

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_workflow_issue_to_pr(self, mock_get_toolkit):
        """Test complete workflow from issue analysis to PR creation."""
        # Mock tools for the workflow
        issues_tool = Mock()
        issues_tool.name = "Get Issues"
        issues_tool.invoke.return_value = "Issue #123: Bug in authentication module"
        
        create_pr_tool = Mock()
        create_pr_tool.name = "Create Pull Request"
        create_pr_tool.invoke.return_value = "PR #456 created successfully"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [issues_tool, create_pr_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        # Step 1: Get issues
        issues_result = github_get_issues.invoke({
            "repository": "test/repo",
            "state": "open"
        })
        
        # Step 2: Create PR to fix issue
        pr_result = github_create_pull_request.invoke({
            "title": "Fix authentication bug",
            "body": "Resolves issue #123",
            "repository": "test/repo"
        })
        
        assert "Issue #123" in issues_result
        assert "PR #456 created successfully" in pr_result
        assert mock_get_toolkit.call_count == 2

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_workflow_code_search_and_file_creation(self, mock_get_toolkit):
        """Test workflow combining code search and file creation."""
        # Mock tools
        search_tool = Mock()
        search_tool.name = "Search code"
        search_tool.invoke.return_value = "Found 3 matches for 'TODO' in codebase"
        
        create_file_tool = Mock()
        create_file_tool.name = "Create File"
        create_file_tool.invoke.return_value = "File created: docs/todo-cleanup.md"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [search_tool, create_file_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        # Step 1: Search for TODOs
        search_result = github_search_code.invoke({
            "query": "TODO",
            "repository": "test/repo"
        })
        
        # Step 2: Create documentation file
        file_result = github_create_file.invoke({
            "file_path": "docs/todo-cleanup.md",
            "content": "# TODO Cleanup Plan\n\nFound 3 TODOs to address...",
            "commit_message": "Add TODO cleanup documentation",
            "repository": "test/repo"
        })
        
        assert "Found 3 matches" in search_result
        assert "File created" in file_result

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_cross_repository_operations(self, mock_get_toolkit):
        """Test operations across multiple repositories."""
        mock_toolkit = Mock()
        
        # Mock different responses for different repositories
        def toolkit_side_effect(repository):
            if repository == "main/repo":
                tools = [Mock()]
                tools[0].name = "Get Issues"
                tools[0].invoke.return_value = "Main repo issues"
                mock_kit = Mock()
                mock_kit.get_tools.return_value = tools
                return mock_kit
            elif repository == "docs/repo":
                tools = [Mock()]
                tools[0].name = "Create File"
                tools[0].invoke.return_value = "Docs file created"
                mock_kit = Mock()
                mock_kit.get_tools.return_value = tools
                return mock_kit
            return None
        
        mock_get_toolkit.side_effect = toolkit_side_effect
        
        # Operations on different repositories
        main_result = github_get_issues.invoke({"repository": "main/repo"})
        docs_result = github_create_file.invoke({
            "repository": "docs/repo",
            "file_path": "summary.md",
            "content": "Project summary",
            "commit_message": "Add summary"
        })
        
        assert "Main repo issues" in main_result
        assert "Docs file created" in docs_result

    @patch('github.Github')  # Patch the actual Github class
    def test_github_repository_creation_workflow(self, mock_github_class):
        """Test repository creation in agent workflow."""
        mock_repo = Mock()
        mock_repo.full_name = "LimbicNode42/new-project"
        mock_repo.html_url = "https://github.com/LimbicNode42/new-project"
        mock_repo.clone_url = "https://github.com/LimbicNode42/new-project.git"
        
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
                "name": "new-project",
                "description": "AI-generated project",
                "private": False
            })
        
        assert "LimbicNode42/new-project" in result
        assert "AI-generated project" in result
        mock_user.create_repo.assert_called_once()

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_error_recovery_workflow(self, mock_get_toolkit):
        """Test error recovery in GitHub workflow."""
        # First call fails, second succeeds
        mock_toolkit_fail = Mock()
        mock_toolkit_fail.get_tools.side_effect = Exception("API rate limit")
        
        mock_tool_success = Mock()
        mock_tool_success.name = "Get Issues"
        mock_tool_success.invoke.return_value = "Issues retrieved after retry"
        
        mock_toolkit_success = Mock()
        mock_toolkit_success.get_tools.return_value = [mock_tool_success]
        
        mock_get_toolkit.side_effect = [mock_toolkit_fail, mock_toolkit_success]
        
        # First attempt fails
        result1 = github_get_issues.invoke({"repository": "test/repo"})
        assert "❌ Error fetching GitHub issues" in result1
        
        # Second attempt succeeds
        result2 = github_get_issues.invoke({"repository": "test/repo"})
        assert "Issues retrieved after retry" in result2

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_concurrent_operations(self, mock_get_toolkit):
        """Test concurrent GitHub operations."""
        import threading
        
        mock_tool = Mock()
        mock_tool.name = "Get Issues"
        mock_tool.invoke.return_value = "Concurrent operation result"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        results = []
        
        def github_worker(repo_suffix):
            result = github_get_issues.invoke({
                "repository": f"test/repo-{repo_suffix}"
            })
            results.append(result)
        
        # Create multiple threads for concurrent operations
        threads = []
        for i in range(3):
            thread = threading.Thread(target=github_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all operations to complete
        for thread in threads:
            thread.join()
        
        assert len(results) == 3
        for result in results:
            assert "Concurrent operation result" in result

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_agent_state_management(self, mock_get_toolkit):
        """Test GitHub tools with agent state management."""
        # Simulate agent state with repository context
        agent_state = {
            "current_repository": "project/main",
            "active_branch": "feature-branch",
            "assigned_issues": [123, 456]
        }
        
        mock_tool = Mock()
        mock_tool.name = "Get Issues"  # Changed to match the tool that github_get_issues looks for
        mock_tool.invoke.return_value = "Issue details from state"
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        # Use repository from agent state
        result = github_get_issues.invoke({
            "repository": agent_state["current_repository"]
        })
        
        assert "project/main" in result
        assert "Issue details from state" in result

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_tool_chaining(self, mock_get_toolkit):
        """Test chaining multiple GitHub tools together."""
        # Mock tools for chaining
        read_tool = Mock()
        read_tool.name = "Read File"
        read_tool.invoke.return_value = "# Current README\n\nOld content"
        
        update_tool = Mock()
        update_tool.name = "Update File"
        update_tool.invoke.return_value = "README.md updated successfully"
        
        # Different tool sets for different calls
        def toolkit_side_effect(repository):
            mock_kit = Mock()
            if mock_get_toolkit.call_count <= 1:
                mock_kit.get_tools.return_value = [read_tool]
            else:
                mock_kit.get_tools.return_value = [update_tool]
            return mock_kit
        
        mock_get_toolkit.side_effect = toolkit_side_effect
        
        # Step 1: Read current file
        from dev_team.tools import github_read_file, github_update_file
        
        read_result = github_read_file.invoke({
            "file_path": "README.md",
            "repository": "test/repo"
        })
        
        # Step 2: Update file based on current content
        update_result = github_update_file.invoke({
            "file_path": "README.md",
            "content": "# Updated README\n\nNew content based on old",
            "commit_message": "Update README with new information",
            "repository": "test/repo"
        })
        
        assert "Old content" in read_result
        assert "updated successfully" in update_result

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_bulk_operations(self, mock_get_toolkit):
        """Test bulk operations across multiple GitHub items."""
        mock_tool = Mock()
        mock_tool.name = "Get Issue"
        
        # Different responses for different issue numbers
        def issue_side_effect(params):
            issue_num = params.get("issue_number", 0)
            return f"Issue #{issue_num} details"
        
        mock_tool.invoke.side_effect = issue_side_effect
        
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = [mock_tool]
        mock_get_toolkit.return_value = mock_toolkit
        
        # Bulk fetch multiple issues
        issue_numbers = [101, 102, 103]
        results = []
        
        for issue_num in issue_numbers:
            from dev_team.tools import github_get_issue
            result = github_get_issue.invoke({
                "issue_number": issue_num,
                "repository": "test/repo"
            })
            results.append(result)
        
        assert len(results) == 3
        assert "Issue #101 details" in results[0]
        assert "Issue #102 details" in results[1]
        assert "Issue #103 details" in results[2]

    def test_github_environment_configuration(self):
        """Test GitHub tools with different environment configurations."""
        # Test with minimal configuration
        with patch.dict(os.environ, {
            "GITHUB_APP_ID": "123456",
            "GITHUB_APP_PRIVATE_KEY": "test_key"
        }, clear=True):
            from dev_team.tools import _get_github_toolkit
            
            with patch('dev_team.tools.GitHubAPIWrapper') as mock_wrapper:
                mock_wrapper.return_value = Mock()
                
                with patch('dev_team.tools.GitHubToolkit') as mock_toolkit:
                    mock_toolkit.from_github_api_wrapper.return_value = Mock()
                    
                    result = _get_github_toolkit()
                    assert result is not None

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_repository_switching(self, mock_get_toolkit):
        """Test switching between repositories during workflow."""
        # Mock different toolkit instances for different repos
        repo_toolkits = {}
        
        def toolkit_side_effect(repository=None):
            if repository not in repo_toolkits:
                mock_tool = Mock()
                mock_tool.name = "Get Issues"
                mock_tool.invoke.return_value = f"Issues from {repository or 'default'}"
                
                mock_kit = Mock()
                mock_kit.get_tools.return_value = [mock_tool]
                repo_toolkits[repository] = mock_kit
            
            return repo_toolkits[repository]
        
        mock_get_toolkit.side_effect = toolkit_side_effect
        
        # Switch between repositories
        repo1_result = github_get_issues.invoke({"repository": "team/backend"})
        repo2_result = github_get_issues.invoke({"repository": "team/frontend"})
        default_result = github_get_issues.invoke({})  # Use default repo
        
        assert "Issues from team/backend" in repo1_result
        assert "Issues from team/frontend" in repo2_result
        assert "Issues from default" in default_result

    @patch('dev_team.tools._get_github_toolkit')
    def test_github_branch_workflow(self, mock_get_toolkit):
        """Test complete branch management workflow."""
        # Mock tools for branch operations
        list_tool = Mock()
        list_tool.name = "List branches in this repository"
        list_tool.invoke.return_value = "main, develop, feature-1"
        
        create_tool = Mock()
        create_tool.name = "Create a new branch"
        create_tool.invoke.return_value = "Branch 'feature-2' created from main"
        
        set_tool = Mock()
        set_tool.name = "Set active branch"
        set_tool.invoke.return_value = "Active branch set to 'feature-2'"
        
        def toolkit_side_effect(repository):
            call_count = mock_get_toolkit.call_count
            mock_kit = Mock()
            if call_count == 1:
                mock_kit.get_tools.return_value = [list_tool]
            elif call_count == 2:
                mock_kit.get_tools.return_value = [create_tool]
            else:
                mock_kit.get_tools.return_value = [set_tool]
            return mock_kit
        
        mock_get_toolkit.side_effect = toolkit_side_effect
        
        # Complete branch workflow
        from dev_team.tools import github_list_branches, github_create_branch, github_set_active_branch
        
        # Step 1: List existing branches
        list_result = github_list_branches.invoke({"repository": "test/repo"})
        
        # Step 2: Create new branch
        create_result = github_create_branch.invoke({
            "branch_name": "feature-2",
            "repository": "test/repo"
        })
        
        # Step 3: Set as active branch
        set_result = github_set_active_branch.invoke({
            "branch_name": "feature-2",
            "repository": "test/repo"
        })
        
        assert "main, develop, feature-1" in list_result
        assert "Branch 'feature-2' created" in create_result
        assert "Active branch set" in set_result
