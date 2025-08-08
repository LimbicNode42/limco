"""LangGraph Organizational Structure with Human-in-the-Loop.

Main graph definition orchestrating:
- Human goal setting and escalation
- Organizational hierarchy and delegation patterns
- Evaluator-optimizer pattern with quality gates
- Parallel processing with aggregation
"""

from __future__ import annotations

import sys
import os
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END

# Add current directory to path to find modules
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import all modules
from states import State

from agents import (
    human_goal_setting, cto, engineering_manager, 
    senior_engineer, qa_engineer, senior_engineer_aggregator, review
)
from evaluators import (
    unit_test_evaluator, self_review_evaluator, peer_review_evaluator,
    integration_test_evaluator, manager_review_evaluator, 
    cto_review_evaluator, human_escalation_evaluator
)
from routing import (
    should_continue_with_managers, should_continue_with_engineers, 
    should_continue_with_evaluation
)


class Configuration(TypedDict):
    """Configurable parameters for organizational structure.

    Set these when creating assistants OR when invoking the graph.
    See: https://langchain-ai.github.io/langgraph/cloud/how-tos/configuration_cloud/
    """

    max_managers: int
    max_senior_engineers_per_manager: int


# Define the graph with proper organizational structure, evaluation pipeline, and human-in-the-loop
graph = (
    StateGraph(State, config_schema=Configuration)
    .add_node("human_goal_setting", human_goal_setting)
    .add_node("cto", cto)
    .add_node("engineering_manager", engineering_manager)
    .add_node("senior_engineer", senior_engineer)
    .add_node("senior_engineer_aggregator", senior_engineer_aggregator)
    .add_node("qa_engineer", qa_engineer)
    
    # Evaluator-Optimizer Pattern Nodes
    .add_node("evaluation", lambda state: {"current_phase": "evaluation"})  # Evaluation entry point
    .add_node("unit_test_evaluator", unit_test_evaluator)
    .add_node("self_review_evaluator", self_review_evaluator)
    .add_node("peer_review_evaluator", peer_review_evaluator)
    .add_node("integration_test_evaluator", integration_test_evaluator)
    .add_node("manager_review_evaluator", manager_review_evaluator)
    .add_node("cto_review_evaluator", cto_review_evaluator)
    .add_node("human_escalation_evaluator", human_escalation_evaluator)  # Human-in-the-loop escalation
    
    .add_node("review", review)
    
    # Human-in-the-loop flow: start with human goal setting
    .add_edge("__start__", "human_goal_setting")
    .add_edge("human_goal_setting", "cto")
    
    # CTO -> Engineering Managers (orchestrator-worker pattern)
    .add_conditional_edges(
        "cto",
        should_continue_with_managers,
        {
            "engineering_manager": "engineering_manager",
            "review": "review"
        }
    )
    
    # Loop for multiple managers (parallel delegation - each works on different manager tasks)
    .add_conditional_edges(
        "engineering_manager",
        should_continue_with_managers,
        {
            "engineering_manager": "engineering_manager",
            "review": "review"
        }
    )
    
    # Engineering Manager -> Engineers (parallel execution patterns)
    .add_conditional_edges(
        "engineering_manager",
        should_continue_with_engineers,
        {
            "senior_engineer": "senior_engineer",           # Multiple senior engineers work in parallel on different dev tasks
            "senior_engineer_aggregator": "senior_engineer_aggregator",  # Combines parallel senior engineer outputs
            "qa_engineer": "qa_engineer",                   # QA tests aggregated outputs
            "evaluation": "evaluation",
            "review": "review"
        }
    )
    
    # Senior Engineers (parallel workers on different development tasks)
    .add_conditional_edges(
        "senior_engineer",
        should_continue_with_engineers,
        {
            "senior_engineer": "senior_engineer",           # Continue parallel processing
            "senior_engineer_aggregator": "senior_engineer_aggregator",  # Aggregate when multiple outputs ready
            "qa_engineer": "qa_engineer",
            "evaluation": "evaluation",
            "review": "review"
        }
    )
    
    # Senior Engineer Aggregator (synthesizes parallel outputs into single deliverable)
    .add_conditional_edges(
        "senior_engineer_aggregator",
        should_continue_with_engineers,
        {
            "senior_engineer": "senior_engineer",
            "senior_engineer_aggregator": "senior_engineer_aggregator",
            "qa_engineer": "qa_engineer",                   # Route to QA for testing aggregated deliverable
            "evaluation": "evaluation",
            "review": "review"
        }
    )
    
    # QA Engineers (1:1 pattern)
    .add_conditional_edges(
        "qa_engineer",
        should_continue_with_engineers,
        {
            "senior_engineer": "senior_engineer",
            "senior_engineer_aggregator": "senior_engineer_aggregator",
            "qa_engineer": "qa_engineer",
            "evaluation": "evaluation",
            "review": "review"
        }
    )
    
    # Evaluation Pipeline (Evaluator-Optimizer Pattern with Human Escalation)
    .add_conditional_edges(
        "evaluation",
        should_continue_with_evaluation,
        {
            "unit_test_evaluator": "unit_test_evaluator",
            "self_review_evaluator": "self_review_evaluator", 
            "peer_review_evaluator": "peer_review_evaluator",
            "integration_test_evaluator": "integration_test_evaluator",
            "manager_review_evaluator": "manager_review_evaluator",
            "cto_review_evaluator": "cto_review_evaluator",
            "human_escalation_evaluator": "human_escalation_evaluator",  # Human intervention
            "execution": "senior_engineer",  # Back to execution
            "review": "review"
        }
    )
    
    # Evaluation stage routing (sequential evaluation with loops and human escalation)
    .add_conditional_edges(
        "unit_test_evaluator",
        should_continue_with_evaluation,
        {
            "unit_test_evaluator": "unit_test_evaluator",
            "self_review_evaluator": "self_review_evaluator",
            "peer_review_evaluator": "peer_review_evaluator",
            "integration_test_evaluator": "integration_test_evaluator",
            "manager_review_evaluator": "manager_review_evaluator",
            "cto_review_evaluator": "cto_review_evaluator",
            "human_escalation_evaluator": "human_escalation_evaluator",
            "execution": "senior_engineer",
            "review": "review"
        }
    )
    
    .add_conditional_edges(
        "self_review_evaluator",
        should_continue_with_evaluation,
        {
            "unit_test_evaluator": "unit_test_evaluator",
            "self_review_evaluator": "self_review_evaluator",
            "peer_review_evaluator": "peer_review_evaluator",
            "integration_test_evaluator": "integration_test_evaluator",
            "manager_review_evaluator": "manager_review_evaluator",
            "cto_review_evaluator": "cto_review_evaluator",
            "human_escalation_evaluator": "human_escalation_evaluator",
            "execution": "senior_engineer",
            "review": "review"
        }
    )
    
    .add_conditional_edges(
        "peer_review_evaluator",
        should_continue_with_evaluation,
        {
            "unit_test_evaluator": "unit_test_evaluator",
            "self_review_evaluator": "self_review_evaluator",
            "peer_review_evaluator": "peer_review_evaluator",
            "integration_test_evaluator": "integration_test_evaluator",
            "manager_review_evaluator": "manager_review_evaluator",
            "cto_review_evaluator": "cto_review_evaluator",
            "human_escalation_evaluator": "human_escalation_evaluator",
            "execution": "senior_engineer",
            "review": "review"
        }
    )
    
    .add_conditional_edges(
        "integration_test_evaluator",
        should_continue_with_evaluation,
        {
            "unit_test_evaluator": "unit_test_evaluator",
            "self_review_evaluator": "self_review_evaluator",
            "peer_review_evaluator": "peer_review_evaluator",
            "integration_test_evaluator": "integration_test_evaluator",
            "manager_review_evaluator": "manager_review_evaluator",
            "cto_review_evaluator": "cto_review_evaluator",
            "human_escalation_evaluator": "human_escalation_evaluator",
            "execution": "senior_engineer",
            "review": "review"
        }
    )
    
    .add_conditional_edges(
        "manager_review_evaluator",
        should_continue_with_evaluation,
        {
            "unit_test_evaluator": "unit_test_evaluator",
            "self_review_evaluator": "self_review_evaluator",
            "peer_review_evaluator": "peer_review_evaluator",
            "integration_test_evaluator": "integration_test_evaluator",
            "manager_review_evaluator": "manager_review_evaluator",
            "cto_review_evaluator": "cto_review_evaluator",
            "human_escalation_evaluator": "human_escalation_evaluator",
            "execution": "senior_engineer",
            "review": "review"
        }
    )
    
    .add_conditional_edges(
        "cto_review_evaluator",
        should_continue_with_evaluation,
        {
            "unit_test_evaluator": "unit_test_evaluator",
            "self_review_evaluator": "self_review_evaluator",
            "peer_review_evaluator": "peer_review_evaluator",
            "integration_test_evaluator": "integration_test_evaluator",
            "manager_review_evaluator": "manager_review_evaluator",
            "cto_review_evaluator": "cto_review_evaluator",
            "human_escalation_evaluator": "human_escalation_evaluator",
            "execution": "senior_engineer",
            "review": "review"
        }
    )
    
    .add_conditional_edges(
        "human_escalation_evaluator",
        should_continue_with_evaluation,
        {
            "unit_test_evaluator": "unit_test_evaluator",
            "self_review_evaluator": "self_review_evaluator",
            "peer_review_evaluator": "peer_review_evaluator",
            "integration_test_evaluator": "integration_test_evaluator",
            "manager_review_evaluator": "manager_review_evaluator",
            "cto_review_evaluator": "cto_review_evaluator",
            "human_escalation_evaluator": "human_escalation_evaluator",
            "execution": "senior_engineer",
            "review": "review"
        }
    )
    
    # End at review
    .add_edge("review", END)
)

# Compile the graph
# Note: LangGraph Studio provides built-in persistence for human-in-the-loop functionality
graph = graph.compile()
