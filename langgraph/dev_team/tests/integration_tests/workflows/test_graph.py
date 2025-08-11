import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, patch

# Add src to Python path for imports
current_dir = Path(__file__).parent.parent.parent
src_dir = current_dir / "src" / "dev_team"
sys.path.insert(0, str(src_dir))

from graph import graph
import states

pytestmark = pytest.mark.anyio


@pytest.mark.langsmith
async def test_graph_basic_execution() -> None:
    """Test basic graph execution with simple input."""
    inputs = {"project_goals": "Create a simple web application"}
    
    # Mock the LLM calls to avoid API dependencies in tests
    with patch('agents.get_model_for_agent') as mock_model:
        mock_response = AsyncMock()
        mock_response.content = "Test response"
        mock_model.return_value.ainvoke = AsyncMock(return_value=mock_response)
        
        res = await graph.ainvoke(inputs)
        assert res is not None
        assert "project_goals" in res


@pytest.mark.langsmith 
async def test_graph_complexity_analysis_flow() -> None:
    """Test graph execution with complexity analysis."""
    inputs = {
        "project_goals": "Build enterprise microservices platform with 15+ services",
        "team_structure": states.ComplexityBasedTeamStructure(
            complexity_score=8.5,
            total_recommended_workers=12,
            requires_iteration=True
        )
    }
    
    with patch('agents.get_model_for_agent') as mock_model:
        mock_response = AsyncMock()
        mock_response.content = "Complex project analysis completed"
        mock_model.return_value.ainvoke = AsyncMock(return_value=mock_response)
        
        res = await graph.ainvoke(inputs)
        assert res is not None
        assert res["team_structure"].complexity_score == 8.5


@pytest.mark.langsmith
async def test_graph_human_assistance_flow() -> None:
    """Test graph execution with human assistance requests."""
    assistance_request = states.HumanAssistanceRequest(
        id="test_req",
        work_item_id="task_001",
        engineer_id="senior_eng_1", 
        request_type="credentials",
        title="AWS Access Required",
        description="Need AWS credentials for deployment"
    )
    
    inputs = {
        "project_goals": "Deploy application requiring AWS access",
        "human_assistance_requests": [assistance_request],
        "pending_human_intervention": True
    }
    
    with patch('agents.get_model_for_agent') as mock_model:
        mock_response = AsyncMock()
        mock_response.content = "Human assistance coordinated"
        mock_model.return_value.ainvoke = AsyncMock(return_value=mock_response)
        
        res = await graph.ainvoke(inputs)
        assert res is not None
        assert len(res["human_assistance_requests"]) >= 1


@pytest.mark.langsmith
async def test_graph_iteration_flow() -> None:
    """Test graph execution with iteration state."""
    iteration_state = states.IterationState(
        is_iterative=True,
        current_iteration=0,
        total_iterations=3,
        iteration_work_batches=[
            ["task_1", "task_2"],
            ["task_3", "task_4"], 
            ["task_5", "task_6"]
        ]
    )
    
    inputs = {
        "project_goals": "Large project requiring multiple iterations",
        "iteration_state": iteration_state
    }
    
    with patch('agents.get_model_for_agent') as mock_model:
        mock_response = AsyncMock()
        mock_response.content = "Iteration management active"
        mock_model.return_value.ainvoke = AsyncMock(return_value=mock_response)
        
        res = await graph.ainvoke(inputs)
        assert res is not None
        assert res["iteration_state"].is_iterative is True


async def test_graph_node_connectivity() -> None:
    """Test that all required nodes are properly connected."""
    # Test that graph has all expected nodes
    node_names = set(graph.nodes.keys())
    
    required_nodes = {
        "human_goal_setting", "cto", "engineering_manager",
        "senior_engineer", "qa_engineer", "capability_gap_analyzer",
        "human_assistance_coordinator", "evaluation", "review"
    }
    
    for node in required_nodes:
        assert node in node_names, f"Required node '{node}' missing from graph"


async def test_graph_with_work_queue() -> None:
    """Test graph execution with work items in queue."""
    work_items = [
        states.WorkItem(
            id="task_1",
            title="Implement authentication",
            description="Add user login/logout",
            priority=5,
            status="pending"
        ),
        states.WorkItem(
            id="task_2", 
            title="Setup database",
            description="Configure PostgreSQL",
            priority=4,
            status="pending"
        )
    ]
    
    inputs = {
        "project_goals": "Build web application with authentication",
        "work_queue": work_items
    }
    
    with patch('agents.get_model_for_agent') as mock_model:
        mock_response = AsyncMock()
        mock_response.content = "Work queue processed"
        mock_model.return_value.ainvoke = AsyncMock(return_value=mock_response)
        
        res = await graph.ainvoke(inputs)
        assert res is not None
        assert len(res["work_queue"]) >= 2
