"""
Integration tests for human assistance workflow.
"""
import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# Add src to Python path for imports
current_dir = Path(__file__).parent.parent.parent
src_dir = current_dir / "src" / "dev_team"
sys.path.insert(0, str(src_dir))

import states
from human_assistance import (
    create_assistance_request, identify_capability_gaps,
    get_pending_assistance_requests
)
from agents import llm_capability_gap_analyzer, llm_human_assistance_coordinator

pytestmark = pytest.mark.anyio


class TestHumanAssistanceWorkflow:
    """Integration tests for the complete human assistance workflow."""
    
    async def test_capability_gap_detection_workflow(self):
        """Test the complete capability gap detection and request creation workflow."""
        # Setup: Create a state with failed work items
        failed_work_item = states.WorkItem(
            id="task_failed",
            title="Deploy to AWS",
            description="Deploy application to AWS ECS",
            status="failed",
            result="Authentication failed: Invalid AWS credentials",
            assigned_to="senior_eng_1"
        )
        
        state = states.State(
            failed_work=[failed_work_item],
            human_assistance_requests=[],
            pending_human_intervention=False
        )
        
        # Mock the model responses
        with patch('agents.get_model_for_agent') as mock_get_model:
            mock_model = AsyncMock()
            mock_response = AsyncMock()
            mock_response.content = "Capability gap analysis completed"
            mock_model.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_model.return_value = mock_model
            
            # Execute capability gap analyzer
            result = await llm_capability_gap_analyzer(state, {})
            
            # Verify assistance request was created
            assert "human_assistance_requests" in result
            assert len(result["human_assistance_requests"]) > 0
            assert result["pending_human_intervention"] is True
            assert result["current_phase"] == "human_assistance"
    
    async def test_human_assistance_coordinator_workflow(self):
        """Test the human assistance coordinator processing workflow."""
        # Setup: Create state with pending assistance requests
        assistance_request = states.HumanAssistanceRequest(
            id="req_001",
            work_item_id="task_001",
            engineer_id="senior_eng_1",
            request_type="credentials",
            title="AWS API Access Required",
            description="Cannot deploy to AWS - missing credentials",
            urgency="high",
            required_capabilities=["AWS CLI", "IAM permissions"],
            blocked_tasks=["Deploy to production"]
        )
        
        state = states.State(
            human_assistance_requests=[assistance_request],
            pending_human_intervention=True,
            current_phase="human_assistance"
        )
        
        # Mock the model responses
        with patch('agents.get_model_for_agent') as mock_get_model:
            mock_model = AsyncMock()
            mock_response = AsyncMock()
            mock_response.content = "Human assistance coordination completed"
            mock_model.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_model.return_value = mock_model
            
            # Execute human assistance coordinator
            result = await llm_human_assistance_coordinator(state, {})
            
            # Verify coordinator processed the requests
            assert result["current_phase"] == "human_assistance"
            assert result["pending_human_intervention"] is True
            assert "implementation_details" in result
            assert "HUMAN ASSISTANCE REQUIRED" in result["implementation_details"]
    
    async def test_capability_gap_identification_integration(self):
        """Test capability gap identification with various error types."""
        test_scenarios = [
            {
                "error": "Authentication failed: Invalid AWS credentials",
                "task": "Deploy to AWS ECS",
                "expected_gap_type": "missing_credentials"
            },
            {
                "error": "Permission denied: Cannot access Docker registry", 
                "task": "Build container images",
                "expected_gap_type": "insufficient_access"
            },
            {
                "error": "Command not found: kubectl",
                "task": "Deploy to Kubernetes",
                "expected_gap_type": "missing_tools"
            },
            {
                "error": "Service unavailable: Database connection refused",
                "task": "Run migrations",
                "expected_gap_type": "platform_unavailable"
            }
        ]
        
        for scenario in test_scenarios:
            gaps = identify_capability_gaps(scenario["error"], scenario["task"])
            
            assert len(gaps) > 0, f"No gaps identified for scenario: {scenario['error']}"
            assert gaps[0].gap_type == scenario["expected_gap_type"], \
                f"Expected {scenario['expected_gap_type']}, got {gaps[0].gap_type}"
    
    async def test_assistance_request_lifecycle(self):
        """Test complete assistance request lifecycle from creation to resolution."""
        # Phase 1: Create assistance request
        request = create_assistance_request(
            work_item_id="task_lifecycle",
            engineer_id="senior_eng_2",
            request_type="access",
            title="Database Access Required",
            description="Need access to staging database for testing",
            urgency="medium",
            required_capabilities=["PostgreSQL access", "VPN connection"],
            blocked_tasks=["Integration testing", "Data validation"]
        )
        
        assert request.status == "pending"
        assert request.resolved_at is None
        
        # Phase 2: Add to state and check detection
        state = states.State(
            human_assistance_requests=[request],
            pending_human_intervention=False  # Initially false
        )
        
        pending_requests = get_pending_assistance_requests(state)
        assert len(pending_requests) == 1
        assert pending_requests[0].id == request.id
        
        # Phase 3: Simulate human resolution
        request.status = "resolved"
        request.human_response = "Database access granted via VPN"
        request.provided_credentials = {"DB_HOST": "staging.db.internal"}
        request.provided_access = ["staging-database", "vpn-access"]
        
        # Phase 4: Verify resolution state
        updated_state = states.State(
            human_assistance_requests=[request],
            pending_human_intervention=False
        )
        
        pending_after_resolution = get_pending_assistance_requests(updated_state)
        assert len(pending_after_resolution) == 0
    
    async def test_multi_request_prioritization(self):
        """Test handling multiple assistance requests with different priorities."""
        requests = [
            states.HumanAssistanceRequest(
                id="req_low",
                work_item_id="task_low",
                engineer_id="eng_1",
                request_type="tools",
                title="Low Priority Request",
                description="Tool installation needed",
                urgency="low"
            ),
            states.HumanAssistanceRequest(
                id="req_critical",
                work_item_id="task_critical",
                engineer_id="eng_2", 
                request_type="credentials",
                title="Critical Production Issue",
                description="Production deployment blocked",
                urgency="critical"
            ),
            states.HumanAssistanceRequest(
                id="req_medium",
                work_item_id="task_medium",
                engineer_id="eng_3",
                request_type="access",
                title="Medium Priority Access",
                description="Staging environment access",
                urgency="medium"
            )
        ]
        
        state = states.State(
            human_assistance_requests=requests,
            pending_human_intervention=True
        )
        
        # Mock the coordinator processing
        with patch('agents.get_model_for_agent') as mock_get_model:
            mock_model = AsyncMock()
            mock_response = AsyncMock()
            mock_response.content = "Prioritized assistance coordination"
            mock_model.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_model.return_value = mock_model
            
            result = await llm_human_assistance_coordinator(state, {})
            
            # Verify the implementation details contain priority information
            implementation_details = result.get("implementation_details", "")
            assert "CRITICAL REQUESTS" in implementation_details
            assert "MEDIUM PRIORITY REQUESTS" in implementation_details
            assert "Critical Production Issue" in implementation_details
    
    async def test_blocked_work_item_handling(self):
        """Test handling of blocked work items that need human assistance."""
        # Create blocked work item
        blocked_work_item = states.WorkItem(
            id="task_blocked",
            title="Deploy to Production",
            description="Deploy application to production environment",
            status="blocked",
            result="BLOCKED - Missing production deployment credentials",
            assigned_to="senior_eng_3"
        )
        
        state = states.State(
            work_queue=[blocked_work_item],
            human_assistance_requests=[],
            pending_human_intervention=False
        )
        
        # Mock capability gap analyzer
        with patch('agents.get_model_for_agent') as mock_get_model:
            mock_model = AsyncMock()
            mock_response = AsyncMock()
            mock_response.content = "Blocked work analysis completed"
            mock_model.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_model.return_value = mock_model
            
            # The analyzer should detect the blocked item and create assistance request
            result = await llm_capability_gap_analyzer(state, {})
            
            # For blocked items, the analyzer should transition to human assistance
            assert result["current_phase"] in ["human_assistance", "execution"]


if __name__ == "__main__":
    pytest.main([__file__])
