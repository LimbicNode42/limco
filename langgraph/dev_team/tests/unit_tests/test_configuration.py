import sys
from pathlib import Path

# Add src to Python path for imports
current_dir = Path(__file__).parent.parent.parent
src_dir = current_dir / "src" / "dev_team"
sys.path.insert(0, str(src_dir))

from langgraph.pregel import Pregel
from graph import graph


def test_graph_is_compiled() -> None:
    """Test that the graph is properly compiled."""
    assert isinstance(graph, Pregel)


def test_graph_has_required_nodes() -> None:
    """Test that the graph contains all required nodes."""
    node_names = set(graph.nodes.keys())
    
    # Core workflow nodes
    required_nodes = {
        "human_goal_setting",
        "cto", 
        "engineering_manager",
        "senior_engineer",
        "qa_engineer",
        "review"
    }
    
    for node in required_nodes:
        assert node in node_names, f"Required node '{node}' not found in graph"


def test_graph_has_human_assistance_nodes() -> None:
    """Test that human assistance nodes are present."""
    node_names = set(graph.nodes.keys())
    
    human_assistance_nodes = {
        "capability_gap_analyzer",
        "human_assistance_coordinator"
    }
    
    for node in human_assistance_nodes:
        assert node in node_names, f"Human assistance node '{node}' not found in graph"


def test_graph_has_evaluation_nodes() -> None:
    """Test that evaluation pipeline nodes are present."""
    node_names = set(graph.nodes.keys())
    
    evaluation_nodes = {
        "evaluation",
        "unit_test_evaluator", 
        "self_review_evaluator",
        "peer_review_evaluator",
        "integration_test_evaluator",
        "manager_review_evaluator",
        "cto_review_evaluator"
    }
    
    for node in evaluation_nodes:
        assert node in node_names, f"Evaluation node '{node}' not found in graph"
