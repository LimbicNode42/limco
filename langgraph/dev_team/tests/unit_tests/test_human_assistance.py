"""
Unit tests for human assistance functionality.
"""
import sys
from pathlib import Path
import pytest
from datetime import datetime
from unittest.mock import MagicMock

# Add src to Python path for imports
current_dir = Path(__file__).parent.parent.parent
src_dir = current_dir / "src" / "dev_team"
sys.path.insert(0, str(src_dir))

from human_assistance import (
    create_assistance_request, identify_capability_gaps, 
    format_assistance_request_summary, resolve_assistance_request,
    get_pending_assistance_requests, check_if_human_intervention_needed,
    create_capability_gap_summary
)
import states


class TestHumanAssistanceRequest:
    """Test HumanAssistanceRequest creation and management."""
    
    def test_create_assistance_request_basic(self):
        """Test creating a basic assistance request."""
        request = create_assistance_request(
            work_item_id="task_001",
            engineer_id="senior_eng_1",
            request_type="credentials",
            title="AWS Access Required",
            description="Need AWS credentials for deployment"
        )
        
        assert request.work_item_id == "task_001"
        assert request.engineer_id == "senior_eng_1"
        assert request.request_type == "credentials"
        assert request.title == "AWS Access Required"
        assert request.status == "pending"
        assert request.urgency == "medium"  # default
        assert request.id is not None
        assert isinstance(request.created_at, datetime)
    
    def test_create_assistance_request_full(self):
        """Test creating assistance request with all parameters."""
        request = create_assistance_request(
            work_item_id="task_002",
            engineer_id="qa_eng_1",
            request_type="access",
            title="Database Access",
            description="Need database access for testing",
            urgency="high",
            required_capabilities=["PostgreSQL access", "VPN connection"],
            blocked_tasks=["Integration tests", "Performance tests"],
            suggested_solution="Request database credentials from DevOps"
        )
        
        assert request.urgency == "high"
        assert len(request.required_capabilities) == 2
        assert len(request.blocked_tasks) == 2
        assert request.suggested_solution is not None
    
    def test_resolve_assistance_request(self):
        """Test resolving an assistance request."""
        request = create_assistance_request(
            work_item_id="task_003",
            engineer_id="senior_eng_2",
            request_type="tools",
            title="Kubernetes CLI",
            description="Need kubectl for deployment"
        )
        
        # Initially pending
        assert request.status == "pending"
        assert request.resolved_at is None
        
        # Resolve it
        resolved_request = resolve_assistance_request(
            request,
            human_response="kubectl installed and configured",
            provided_credentials={"KUBECONFIG": "/path/to/config"},
            provided_access=["kubernetes-cluster"],
            notes=["Version 1.28.0 installed", "Config valid for 30 days"]
        )
        
        assert resolved_request.status == "resolved"
        assert resolved_request.human_response == "kubectl installed and configured"
        assert "KUBECONFIG" in resolved_request.provided_credentials
        assert "kubernetes-cluster" in resolved_request.provided_access
        assert len(resolved_request.notes) == 2
        assert resolved_request.resolved_at is not None


class TestCapabilityGapIdentification:
    """Test capability gap identification logic."""
    
    def test_identify_missing_credentials(self):
        """Test identifying missing credentials gaps."""
        error_msg = "Authentication failed: Invalid AWS credentials"
        task_desc = "Deploy application to AWS ECS"
        
        gaps = identify_capability_gaps(error_msg, task_desc)
        
        assert len(gaps) == 1
        assert gaps[0].gap_type == "missing_credentials"
        assert gaps[0].impact_level == "medium"
    
    def test_identify_insufficient_access(self):
        """Test identifying access permission gaps."""
        error_msg = "Permission denied: Insufficient privileges to access database"
        task_desc = "Run database migrations"
        
        gaps = identify_capability_gaps(error_msg, task_desc)
        
        assert len(gaps) == 1
        assert gaps[0].gap_type == "insufficient_access"
    
    def test_identify_missing_tools(self):
        """Test identifying missing tools gaps."""
        error_msg = "Command not found: docker"
        task_desc = "Build container images"
        
        gaps = identify_capability_gaps(error_msg, task_desc)
        
        assert len(gaps) == 1
        assert gaps[0].gap_type == "missing_tools"
        assert gaps[0].alternative_available is True  # Tools often have alternatives
    
    def test_identify_platform_unavailable(self):
        """Test identifying platform availability gaps."""
        error_msg = "Service unavailable: Cannot connect to Kubernetes cluster"
        task_desc = "Deploy to staging environment"
        
        gaps = identify_capability_gaps(error_msg, task_desc)
        
        assert len(gaps) == 1
        assert gaps[0].gap_type == "platform_unavailable"
    
    def test_identify_no_gaps(self):
        """Test when no capability gaps are identified."""
        error_msg = "Syntax error in code"
        task_desc = "Fix compilation errors"
        
        gaps = identify_capability_gaps(error_msg, task_desc)
        
        assert len(gaps) == 0
    
    def test_impact_level_assessment(self):
        """Test impact level assessment for different scenarios."""
        # High impact for production/security tasks
        high_impact_gaps = identify_capability_gaps(
            "Authentication failed", 
            "Deploy critical security patch to production"
        )
        if high_impact_gaps:
            assert high_impact_gaps[0].impact_level == "high"
        
        # Medium impact for general access issues
        medium_impact_gaps = identify_capability_gaps(
            "Access denied",
            "Update development database"
        )
        if medium_impact_gaps:
            assert medium_impact_gaps[0].impact_level == "medium"


class TestAssistanceRequestFormatting:
    """Test assistance request formatting for human review."""
    
    def test_format_assistance_request_summary(self):
        """Test formatting assistance request for human review."""
        request = create_assistance_request(
            work_item_id="task_004",
            engineer_id="senior_eng_3",
            request_type="credentials",
            title="API Keys Required",
            description="Need API keys for third-party service integration",
            urgency="critical",
            required_capabilities=["ServiceX API key", "Rate limiting config"],
            blocked_tasks=["Payment processing", "User notifications"]
        )
        
        summary = format_assistance_request_summary(request)
        
        assert "🔴" in summary  # Critical urgency emoji
        assert "🔑" in summary  # Credentials type emoji
        assert "API Keys Required" in summary
        assert "senior_eng_3" in summary
        assert "Critical" in summary
        assert "ServiceX API key" in summary
        assert "Payment processing" in summary
    
    def test_format_different_request_types(self):
        """Test formatting different request types."""
        request_types = [
            ("credentials", "🔑"),
            ("access", "🚪"),
            ("tools", "🔧"),
            ("platform", "🖥️"),
            ("approval", "✅")
        ]
        
        for req_type, expected_emoji in request_types:
            request = create_assistance_request(
                work_item_id=f"task_{req_type}",
                engineer_id="test_eng",
                request_type=req_type,
                title=f"Test {req_type}",
                description=f"Test {req_type} request"
            )
            
            summary = format_assistance_request_summary(request)
            assert expected_emoji in summary


class TestStateIntegration:
    """Test integration with state management."""
    
    def test_get_pending_assistance_requests(self):
        """Test getting pending assistance requests from state."""
        # Create test requests
        pending_request = create_assistance_request(
            work_item_id="task_005",
            engineer_id="eng_1",
            request_type="access",
            title="Pending Request",
            description="Test pending request"
        )
        
        resolved_request = create_assistance_request(
            work_item_id="task_006",
            engineer_id="eng_2", 
            request_type="tools",
            title="Resolved Request",
            description="Test resolved request"
        )
        resolved_request.status = "resolved"
        
        # Create state with requests
        state = states.State(
            human_assistance_requests=[pending_request, resolved_request]
        )
        
        pending = get_pending_assistance_requests(state)
        
        assert len(pending) == 1
        assert pending[0].title == "Pending Request"
        assert pending[0].status == "pending"
    
    def test_check_if_human_intervention_needed(self):
        """Test checking if human intervention is needed."""
        # State with no requests
        empty_state = states.State()
        assert check_if_human_intervention_needed(empty_state) is False
        
        # State with resolved requests only
        resolved_request = create_assistance_request(
            work_item_id="task_007",
            engineer_id="eng_3",
            request_type="approval",
            title="Resolved Request",
            description="Test resolved"
        )
        resolved_request.status = "resolved"
        
        resolved_state = states.State(
            human_assistance_requests=[resolved_request]
        )
        assert check_if_human_intervention_needed(resolved_state) is False
        
        # State with pending requests
        pending_request = create_assistance_request(
            work_item_id="task_008",
            engineer_id="eng_4",
            request_type="credentials",
            title="Pending Request",
            description="Test pending"
        )
        
        pending_state = states.State(
            human_assistance_requests=[pending_request]
        )
        assert check_if_human_intervention_needed(pending_state) is True
    
    def test_create_capability_gap_summary(self):
        """Test creating capability gap summaries."""
        gaps = [
            states.CapabilityGap(
                gap_type="missing_credentials",
                resource_name="AWS_API_KEY",
                description="AWS credentials missing",
                impact_level="high"
            ),
            states.CapabilityGap(
                gap_type="missing_tools",
                resource_name="kubectl",
                description="Kubernetes CLI not available",
                impact_level="medium",
                alternative_available=True,
                alternative_description="Use web console"
            )
        ]
        
        summary = create_capability_gap_summary(gaps)
        
        assert "2 capability gap(s)" in summary
        assert "Missing Credentials" in summary  # Title case in summary
        assert "AWS_API_KEY" in summary
        assert "High" in summary
        assert "Alternative: Use web console" in summary
    
    def test_empty_capability_gap_summary(self):
        """Test capability gap summary with no gaps."""
        summary = create_capability_gap_summary([])
        assert "No capability gaps identified" in summary


if __name__ == "__main__":
    pytest.main([__file__])
