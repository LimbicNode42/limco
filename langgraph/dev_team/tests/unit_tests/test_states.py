"""
Unit tests for states and data structures.
"""
import sys
from pathlib import Path
import pytest
from datetime import datetime

# Add src to Python path for imports
current_dir = Path(__file__).parent.parent.parent
src_dir = current_dir / "src" / "dev_team"
sys.path.insert(0, str(src_dir))

import states


class TestWorkItem:
    """Test WorkItem data structure."""
    
    def test_work_item_creation(self):
        """Test creating a work item with basic parameters."""
        work_item = states.WorkItem(
            id="task_001",
            title="Implement user authentication",
            description="Add login/logout functionality",
            priority=5
        )
        
        assert work_item.id == "task_001"
        assert work_item.title == "Implement user authentication"
        assert work_item.priority == 5
        assert work_item.status == "pending"  # default
        assert work_item.assigned_to is None  # default
        assert work_item.iteration_batch == 0  # default
    
    def test_work_item_with_evaluation_loop(self):
        """Test work item with evaluation loop."""
        work_item = states.WorkItem(
            id="task_002",
            title="Database migration",
            description="Migrate to PostgreSQL",
            priority=4,
            status="in_evaluation"
        )
        
        assert isinstance(work_item.evaluation_loop, states.EvaluationLoop)
        assert work_item.evaluation_loop.current_stage == "development"
        assert work_item.evaluation_loop.loop_count == 0
    
    def test_work_item_assignment(self):
        """Test work item assignment tracking."""
        work_item = states.WorkItem(
            id="task_003",
            title="API integration",
            description="Integrate payment API",
            assigned_to="senior_eng_1",
            status="assigned",
            created_by="engineering_manager_1"
        )
        
        assert work_item.assigned_to == "senior_eng_1"
        assert work_item.status == "assigned"
        assert work_item.created_by == "engineering_manager_1"


class TestEvaluationLoop:
    """Test EvaluationLoop state tracking."""
    
    def test_evaluation_loop_defaults(self):
        """Test evaluation loop default values."""
        loop = states.EvaluationLoop()
        
        assert loop.current_stage == "development"
        assert loop.loop_count == 0
        assert loop.max_loops == 3
        assert loop.escalation_count == 0
        assert loop.max_escalations == 3
        assert len(loop.feedback) == 0
        assert loop.evaluator == ""
    
    def test_evaluation_loop_progression(self):
        """Test evaluation loop progression tracking."""
        loop = states.EvaluationLoop(
            current_stage="unit_test",
            loop_count=1,
            evaluator="unit_test_evaluator",
            feedback=["Test coverage insufficient"]
        )
        
        assert loop.current_stage == "unit_test"
        assert loop.loop_count == 1
        assert loop.evaluator == "unit_test_evaluator"
        assert len(loop.feedback) == 1
        assert "insufficient" in loop.feedback[0]


class TestComplexityBasedTeamStructure:
    """Test ComplexityBasedTeamStructure data structure."""
    
    def test_team_structure_defaults(self):
        """Test team structure default values."""
        structure = states.ComplexityBasedTeamStructure()
        
        assert structure.recommended_managers == 1
        assert structure.recommended_engineers_per_manager == 2
        assert structure.total_recommended_workers == 3
        assert structure.complexity_score == 5.0
        assert structure.requires_iteration is False
        assert structure.iteration_strategy is None
    
    def test_team_structure_complex_project(self):
        """Test team structure for complex project."""
        structure = states.ComplexityBasedTeamStructure(
            recommended_managers=3,
            recommended_engineers_per_manager=4,
            total_recommended_workers=12,
            complexity_score=8.5,
            requires_iteration=True,
            iteration_strategy="Split into 3 iterations of 4 workers each",
            analysis_reasoning="High complexity enterprise platform requiring parallel development"
        )
        
        assert structure.recommended_managers == 3
        assert structure.total_recommended_workers == 12
        assert structure.complexity_score == 8.5
        assert structure.requires_iteration is True
        assert "iterations" in structure.iteration_strategy


class TestIterationState:
    """Test IterationState management."""
    
    def test_iteration_state_defaults(self):
        """Test iteration state default values."""
        state = states.IterationState()
        
        assert state.is_iterative is False
        assert state.current_iteration == 0
        assert state.total_iterations == 1
        assert len(state.iteration_work_batches) == 0
        assert len(state.iteration_results) == 0
        assert len(state.iteration_summaries) == 0
    
    def test_iteration_state_multi_iteration(self):
        """Test iteration state for multi-iteration project."""
        state = states.IterationState(
            is_iterative=True,
            current_iteration=1,
            total_iterations=3,
            iteration_work_batches=[
                ["task_1", "task_2"],
                ["task_3", "task_4"],
                ["task_5", "task_6"]
            ],
            iteration_summaries=["Iteration 1 completed", "Iteration 2 in progress"]
        )
        
        assert state.is_iterative is True
        assert state.current_iteration == 1
        assert state.total_iterations == 3
        assert len(state.iteration_work_batches) == 3
        assert len(state.iteration_work_batches[0]) == 2


class TestHumanAssistanceRequest:
    """Test HumanAssistanceRequest data structure."""
    
    def test_assistance_request_creation(self):
        """Test creating assistance request."""
        request = states.HumanAssistanceRequest(
            id="req_001",
            work_item_id="task_001",
            engineer_id="senior_eng_1",
            request_type="credentials",
            title="AWS Access Required",
            description="Need AWS credentials for deployment",
            urgency="high"
        )
        
        assert request.id == "req_001"
        assert request.work_item_id == "task_001"
        assert request.engineer_id == "senior_eng_1"
        assert request.request_type == "credentials"
        assert request.urgency == "high"
        assert request.status == "pending"  # default
        assert len(request.required_capabilities) == 0  # default
        assert len(request.blocked_tasks) == 0  # default
    
    def test_assistance_request_full_context(self):
        """Test assistance request with full context."""
        request = states.HumanAssistanceRequest(
            id="req_002",
            work_item_id="task_002",
            engineer_id="qa_eng_1",
            request_type="access",
            title="Database Access",
            description="Need staging database access",
            urgency="critical",
            required_capabilities=["PostgreSQL access", "VPN connection"],
            blocked_tasks=["Integration testing", "Data validation"],
            suggested_solution="Request database credentials from DevOps team"
        )
        
        assert len(request.required_capabilities) == 2
        assert len(request.blocked_tasks) == 2
        assert request.suggested_solution is not None
        assert "PostgreSQL" in request.required_capabilities[0]
    
    def test_assistance_request_resolution(self):
        """Test assistance request resolution tracking."""
        request = states.HumanAssistanceRequest(
            id="req_003",
            work_item_id="task_003",
            engineer_id="senior_eng_2",
            request_type="tools",
            title="Kubernetes CLI",
            description="Need kubectl for deployment"
        )
        
        # Initially unresolved
        assert request.status == "pending"
        assert request.resolved_at is None
        assert request.human_response is None
        
        # Simulate resolution
        request.status = "resolved"
        request.resolved_at = datetime.now()
        request.human_response = "kubectl installed and configured"
        request.provided_credentials = {"KUBECONFIG": "/path/to/config"}
        request.provided_access = ["kubernetes-cluster"]
        request.notes = ["Version 1.28.0", "Valid for 30 days"]
        
        assert request.status == "resolved"
        assert request.resolved_at is not None
        assert "kubectl" in request.human_response
        assert "KUBECONFIG" in request.provided_credentials
        assert len(request.notes) == 2


class TestCapabilityGap:
    """Test CapabilityGap data structure."""
    
    def test_capability_gap_creation(self):
        """Test creating capability gap."""
        gap = states.CapabilityGap(
            gap_type="missing_credentials",
            resource_name="AWS_API_KEY",
            description="AWS credentials not configured",
            impact_level="high"
        )
        
        assert gap.gap_type == "missing_credentials"
        assert gap.resource_name == "AWS_API_KEY"
        assert gap.impact_level == "high"
        assert gap.alternative_available is False  # default
    
    def test_capability_gap_with_alternative(self):
        """Test capability gap with alternative solution."""
        gap = states.CapabilityGap(
            gap_type="missing_tools",
            resource_name="docker",
            description="Docker not installed",
            impact_level="medium",
            alternative_available=True,
            alternative_description="Use podman as container runtime"
        )
        
        assert gap.alternative_available is True
        assert gap.alternative_description is not None
        assert "podman" in gap.alternative_description


class TestState:
    """Test main State management."""
    
    def test_state_defaults(self):
        """Test state default values."""
        state = states.State()
        
        assert state.name == "Dev Team"
        assert state.start_node == "__start__"
        assert state.current_phase == "vision"
        assert len(state.work_queue) == 0
        assert len(state.active_managers) == 0
        assert len(state.completed_work) == 0
        assert len(state.human_assistance_requests) == 0
        assert state.pending_human_intervention is False
    
    def test_state_with_work_items(self):
        """Test state with work items."""
        work_items = [
            states.WorkItem(id="1", title="Task 1", description="Test 1"),
            states.WorkItem(id="2", title="Task 2", description="Test 2")
        ]
        
        state = states.State(
            work_queue=work_items,
            current_phase="execution",
            active_managers=["manager_1"],
            active_engineers={"manager_1": ["eng_1", "eng_2"]}
        )
        
        assert len(state.work_queue) == 2
        assert state.current_phase == "execution"
        assert len(state.active_managers) == 1
        assert "manager_1" in state.active_engineers
        assert len(state.active_engineers["manager_1"]) == 2
    
    def test_state_with_human_assistance(self):
        """Test state with human assistance requests."""
        assistance_requests = [
            states.HumanAssistanceRequest(
                id="req_1",
                work_item_id="task_1",
                engineer_id="eng_1",
                request_type="credentials",
                title="Test Request",
                description="Test assistance"
            )
        ]
        
        state = states.State(
            human_assistance_requests=assistance_requests,
            pending_human_intervention=True,
            current_phase="human_assistance"
        )
        
        assert len(state.human_assistance_requests) == 1
        assert state.pending_human_intervention is True
        assert state.current_phase == "human_assistance"
    
    def test_state_with_team_structure(self):
        """Test state with complexity-based team structure."""
        team_structure = states.ComplexityBasedTeamStructure(
            recommended_managers=2,
            recommended_engineers_per_manager=3,
            total_recommended_workers=6,
            complexity_score=7.5,
            requires_iteration=False
        )
        
        iteration_state = states.IterationState(
            is_iterative=False,
            current_iteration=0,
            total_iterations=1
        )
        
        state = states.State(
            team_structure=team_structure,
            iteration_state=iteration_state,
            current_phase="delegation"
        )
        
        assert state.team_structure.total_recommended_workers == 6
        assert state.team_structure.complexity_score == 7.5
        assert state.iteration_state.is_iterative is False
        assert state.current_phase == "delegation"


if __name__ == "__main__":
    pytest.main([__file__])
