"""
Tests for human-in-the-loop repository selection tools.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from dev_team.tools import (
    request_repository_selection,
    process_repository_choice,
    list_available_repositories,
    initiate_project_workflow
)


class TestRepositorySelectionTools:
    """Test repository selection and human interaction tools."""
    
    def test_request_repository_selection_basic(self):
        """Test basic repository selection request."""
        result = request_repository_selection.invoke({
            "project_description": "Test project"
        })
        
        assert "HUMAN INPUT REQUIRED" in result
        assert "Test project" in result
        assert "use-repo:" in result
        assert "create-repo:" in result
        
    def test_request_repository_selection_with_suggestion(self):
        """Test repository selection with suggested name."""
        result = request_repository_selection.invoke({
            "project_description": "AI Assistant Tool",
            "suggested_name": "ai-assistant-tool"
        })
        
        assert "AI Assistant Tool" in result
        assert "ai-assistant-tool" in result
        assert "Suggested name" in result
        
    def test_initiate_project_workflow_basic(self):
        """Test project workflow initiation."""
        result = initiate_project_workflow.invoke({
            "project_description": "Web scraping tool"
        })
        
        assert "PROJECT WORKFLOW INITIATED" in result
        assert "Web scraping tool" in result
        assert "Repository Selection Required" in result
        assert "Option A: Use Existing Repository" in result
        assert "Option B: Create New Repository" in result
        
    def test_initiate_project_workflow_with_suggestion(self):
        """Test project workflow with suggested repository name."""
        result = initiate_project_workflow.invoke({
            "project_description": "Machine learning pipeline",
            "suggested_repo_name": "ml-pipeline-v2"
        })
        
        assert "Machine learning pipeline" in result
        assert "ml-pipeline-v2" in result
        assert "Suggested name: ml-pipeline-v2" in result


class TestRepositoryChoiceProcessing:
    """Test processing of human repository choices."""
    
    @patch('dev_team.tools._get_github_toolkit')
    def test_process_use_existing_repo_success(self, mock_toolkit):
        """Test processing choice to use existing repository."""
        # Mock successful repository access
        mock_repo_tool = Mock()
        mock_repo_tool.name = "Get Repository"
        mock_repo_tool.run.return_value = "Repository details"
        
        mock_toolkit_instance = Mock()
        mock_toolkit_instance.get_tools.return_value = [mock_repo_tool]
        mock_toolkit.return_value = mock_toolkit_instance
        
        result = process_repository_choice.invoke({
            "human_response": "use-repo: owner/test-repo"
        })
        
        assert "Repository 'owner/test-repo' found and accessible" in result
        assert "Next Steps" in result
        assert "feature branches" in result
        
    @patch('dev_team.tools._get_github_toolkit')
    def test_process_use_existing_repo_not_found(self, mock_toolkit):
        """Test processing choice for non-existent repository."""
        mock_toolkit.return_value = None
        
        result = process_repository_choice.invoke({
            "human_response": "use-repo: owner/nonexistent"
        })
        
        assert "Could not access repository 'owner/nonexistent'" in result
        assert "verify the name and permissions" in result
        
    def test_process_create_new_repo(self):
        """Test processing choice to create new repository."""
        result = process_repository_choice.invoke({
            "human_response": "create-repo: my-awesome-project"
        })
        
        assert "Repository Creation Requested" in result
        assert "my-awesome-project" in result
        assert "github_create_repository" in result
        assert "Next Steps" in result
        
    def test_process_invalid_repo_format(self):
        """Test processing invalid repository format."""
        result = process_repository_choice.invoke({
            "human_response": "use-repo: invalidformat"
        })
        
        assert "Invalid repository format" in result
        assert "owner/repository-name" in result
        
    def test_process_invalid_repo_name(self):
        """Test processing invalid repository name for creation."""
        result = process_repository_choice.invoke({
            "human_response": "create-repo: invalid name with spaces"
        })
        
        assert "Invalid repository name" in result
        assert "lowercase letters" in result
        
    def test_process_invalid_response_format(self):
        """Test processing completely invalid response."""
        result = process_repository_choice.invoke({
            "human_response": "invalid response"
        })
        
        assert "Invalid response format" in result
        assert "use-repo:" in result
        assert "create-repo:" in result
        
    def test_process_case_insensitive(self):
        """Test processing is case insensitive."""
        result = process_repository_choice.invoke({
            "human_response": "USE-REPO: Owner/Test-Repo"
        })
        
        # Should not fail due to case
        assert "Could not access repository" in result or "found and accessible" in result


class TestRepositoryListing:
    """Test repository listing functionality."""
    
    @patch('dev_team.tools._get_github_toolkit')
    def test_list_available_repositories_success(self, mock_toolkit):
        """Test successful repository listing."""
        mock_toolkit.return_value = Mock()
        
        result = list_available_repositories.invoke({})
        
        assert "Available Repositories" in result
        assert "github.com/settings/repositories" in result
        assert "use-repo:" in result
        assert "create-repo:" in result
        
    @patch('dev_team.tools._get_github_toolkit')
    def test_list_repositories_no_connection(self, mock_toolkit):
        """Test repository listing with no GitHub connection."""
        mock_toolkit.return_value = None
        
        result = list_available_repositories.invoke({})
        
        assert "Failed to initialize GitHub connection" in result
        
    @patch('dev_team.tools._get_github_toolkit')
    def test_list_repositories_with_parameters(self, mock_toolkit):
        """Test repository listing with custom parameters."""
        mock_toolkit.return_value = Mock()
        
        result = list_available_repositories.invoke({
            "include_private": False,
            "limit": 10
        })
        
        # Should handle parameters gracefully
        assert "Available Repositories" in result


class TestErrorHandling:
    """Test error handling in human-in-the-loop tools."""
    
    @patch('dev_team.tools._get_github_toolkit')
    def test_process_choice_with_exception(self, mock_toolkit):
        """Test handling of exceptions during choice processing."""
        mock_toolkit.side_effect = Exception("GitHub API error")
        
        result = process_repository_choice.invoke({
            "human_response": "use-repo: owner/test"
        })
        
        assert "Error processing repository choice" in result
        assert "GitHub API error" in result
        
    @patch('dev_team.tools._get_github_toolkit')
    def test_list_repositories_with_exception(self, mock_toolkit):
        """Test handling of exceptions during repository listing."""
        mock_toolkit.side_effect = Exception("Connection failed")
        
        result = list_available_repositories.invoke({})
        
        assert "Error listing repositories" in result
        assert "Connection failed" in result


class TestWorkflowIntegration:
    """Test integration of workflow tools."""
    
    def test_workflow_provides_complete_guidance(self):
        """Test that workflow provides complete guidance."""
        result = initiate_project_workflow.invoke({
            "project_description": "Test project"
        })
        
        # Check for all required workflow elements
        assert "PROJECT WORKFLOW INITIATED" in result
        assert "Repository Selection Required" in result
        assert "REQUIRED ACTION" in result
        assert "After Repository Selection" in result
        assert "feature branches" in result
        assert "pull requests" in result
        
    def test_repository_selection_message_format(self):
        """Test repository selection message format."""
        result = request_repository_selection.invoke({
            "project_description": "Test"
        })
        
        # Verify proper formatting
        lines = result.split('\n')
        assert any("HUMAN INPUT REQUIRED" in line for line in lines)
        assert any("Please respond with" in line for line in lines)
        assert any("use-repo:" in line for line in lines)
        assert any("create-repo:" in line for line in lines)


if __name__ == "__main__":
    pytest.main([__file__])
