"""LangGraph Organizational Structure with LLM-Powered Agents and Human-in-the-Loop.

Enhanced graph definition orchestrating:
- LLM-powered agents with model hierarchies and rate limiting
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

# Import LLM-powered agents
from agents import (
    llm_human_goal_setting, llm_cto, llm_engineering_manager, 
    llm_senior_engineer, llm_qa_engineer, llm_senior_engineer_aggregator, 
    llm_review, llm_iteration_manager, llm_human_assistance_coordinator, 
    llm_capability_gap_analyzer
)

# Import evaluators (keeping original for now)
from evaluators import (
    unit_test_evaluator, self_review_evaluator, peer_review_evaluator,
    integration_test_evaluator, manager_review_evaluator, 
    cto_review_evaluator, human_escalation_evaluator
)

# Import routing logic
from routing import (
    should_continue_with_managers, should_continue_with_engineers, 
    should_continue_with_evaluation, should_route_from_human_assistance
)


class Configuration(TypedDict):
    """Configurable parameters for organizational structure with LLM integration.

    Set these when creating assistants OR when invoking the graph.
    See: https://langchain-ai.github.io/langgraph/cloud/how-tos/configuration_cloud/
    """

    max_managers: int
    max_senior_engineers_per_manager: int


# Define the LLM-powered graph with proper organizational structure, evaluation pipeline, and human-in-the-loop
llm_graph = (
    StateGraph(State, config_schema=Configuration)
    # LLM-powered core agents
    .add_node("human_goal_setting", llm_human_goal_setting)
    .add_node("cto", llm_cto)
    .add_node("engineering_manager", llm_engineering_manager)
    .add_node("senior_engineer", llm_senior_engineer)
    .add_node("senior_engineer_aggregator", llm_senior_engineer_aggregator)
    .add_node("qa_engineer", llm_qa_engineer)
    .add_node("iteration_manager", llm_iteration_manager)  # Manages iteration transitions
    
    # Human assistance nodes for capability gaps
    .add_node("capability_gap_analyzer", llm_capability_gap_analyzer)
    .add_node("human_assistance_coordinator", llm_human_assistance_coordinator)
    
    # Evaluator-Optimizer Pattern Nodes (keeping original evaluators for now)
    .add_node("evaluation", lambda state: {"current_phase": "evaluation"})  # Evaluation entry point
    .add_node("unit_test_evaluator", unit_test_evaluator)
    .add_node("self_review_evaluator", self_review_evaluator)
    .add_node("peer_review_evaluator", peer_review_evaluator)
    .add_node("integration_test_evaluator", integration_test_evaluator)
    .add_node("manager_review_evaluator", manager_review_evaluator)
    .add_node("cto_review_evaluator", cto_review_evaluator)
    .add_node("human_escalation_evaluator", human_escalation_evaluator)  # Human-in-the-loop escalation
    
    .add_node("review", llm_review)
    
    # Human-in-the-loop flow: start with LLM-enhanced human goal setting
    .add_edge("__start__", "human_goal_setting")
    .add_edge("human_goal_setting", "cto")
    
    # LLM CTO -> Engineering Managers (orchestrator-worker pattern with iteration support)
    .add_conditional_edges(
        "cto",
        should_continue_with_managers,
        {
            "engineering_manager": "engineering_manager",
            "execution": "senior_engineer",  # Direct to execution for iterations
            "cto": "cto",  # Loop back for next iteration setup
            "review": "review"
        }
    )
    
    # Loop for multiple LLM managers (parallel delegation with iteration support)
    .add_conditional_edges(
        "engineering_manager",
        should_continue_with_managers,
        {
            "engineering_manager": "engineering_manager",
            "execution": "senior_engineer",
            "cto": "cto",  # Return to CTO for next iteration
            "review": "review"
        }
    )
    
    # LLM Engineering Manager -> Engineers (parallel execution patterns with iteration support)
    .add_conditional_edges(
        "engineering_manager",
        should_continue_with_engineers,
        {
            "senior_engineer": "senior_engineer",           # Multiple LLM senior engineers work in parallel
            "senior_engineer_aggregator": "senior_engineer_aggregator",  # Combines parallel outputs
            "qa_engineer": "qa_engineer",                   # LLM QA tests aggregated outputs
            "evaluation": "evaluation",
            "capability_gap_analyzer": "capability_gap_analyzer",  # Analyze capability gaps
            "human_assistance_coordinator": "human_assistance_coordinator",  # Coordinate human assistance
            "cto": "cto",  # Return to CTO for next iteration
            "review": "review"
        }
    )
    
    # LLM Senior Engineers (parallel workers on different development tasks with iteration support)
    .add_conditional_edges(
        "senior_engineer",
        should_continue_with_engineers,
        {
            "senior_engineer": "senior_engineer",           # Continue parallel processing
            "senior_engineer_aggregator": "senior_engineer_aggregator",  # Aggregate when outputs ready
            "qa_engineer": "qa_engineer",
            "evaluation": "evaluation",
            "cto": "cto",  # Return to CTO for next iteration
            "review": "review"
        }
    )
    
    # LLM Senior Engineer Aggregator (synthesizes parallel outputs with iteration support)
    .add_conditional_edges(
        "senior_engineer_aggregator",
        should_continue_with_engineers,
        {
            "senior_engineer": "senior_engineer",
            "senior_engineer_aggregator": "senior_engineer_aggregator",
            "qa_engineer": "qa_engineer",                   # Route to LLM QA for testing
            "evaluation": "evaluation",
            "cto": "cto",  # Return to CTO for next iteration
            "review": "review"
        }
    )
    
    # LLM QA Engineers (1:1 pattern with iteration support)
    .add_conditional_edges(
        "qa_engineer",
        should_continue_with_engineers,
        {
            "senior_engineer": "senior_engineer",
            "senior_engineer_aggregator": "senior_engineer_aggregator",
            "qa_engineer": "qa_engineer",
            "evaluation": "evaluation",
            "cto": "cto",  # Return to CTO for next iteration
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
            "capability_gap_analyzer": "capability_gap_analyzer",  # Analyze failed work for capability gaps
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
    
    # Human assistance workflow routing
    .add_conditional_edges(
        "capability_gap_analyzer",
        should_route_from_human_assistance,
        {
            "execution": "senior_engineer",
            "capability_gap_analyzer": "capability_gap_analyzer",
            "review": "review"
        }
    )
    
    .add_conditional_edges(
        "human_assistance_coordinator",
        should_route_from_human_assistance,
        {
            "execution": "senior_engineer",
            "capability_gap_analyzer": "capability_gap_analyzer",
            "review": "review"
        }
    )
    
    # End at LLM review
    .add_edge("review", END)
)

# Compile the LLM-powered graph
# Note: LangGraph Studio provides built-in persistence for human-in-the-loop functionality
graph = llm_graph.compile()

__all__ = ["graph", "llm_graph", "Configuration"]
