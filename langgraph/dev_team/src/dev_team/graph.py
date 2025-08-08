"""LangGraph Organizational Structure Testing.

Simplified implementation focusing on:
- Organizational hierarchy and delegation patterns
- Work distribution across managers and engineers  
- Clear visibility into team structure and assignments
"""

from __future__ import annotations

from typing import Any, Dict, Literal
from typing_extensions import TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END

# Add current directory to path to find goals module
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import goals

class Configuration(TypedDict):
    """Configurable parameters for organizational structure.

    Set these when creating assistants OR when invoking the graph.
    See: https://langchain-ai.github.io/langgraph/cloud/how-tos/configuration_cloud/
    """

    max_managers: int
    max_senior_engineers_per_manager: int


def human_goal_setting(state: goals.State, config: RunnableConfig) -> Dict[str, Any]:
    """Human sets project goals at the beginning of the workflow.
    
    This function serves as the human-in-the-loop entry point for goal setting.
    In LangGraph Studio, this would present an interactive form for goal input.
    """
    print("� Human Goal Setting Stage")
    print("=" * 50)
    print("Awaiting human input for project goals...")
    print("This is where the human would define:")
    print("- Project objectives")
    print("- Technical requirements") 
    print("- Success criteria")
    print("- Timeline and constraints")
    
    # For demo purposes, return sample project goals
    # In LangGraph Studio, this would be replaced with actual human input
    sample_goals = """
    Project: AI-Powered Customer Support System
    
    Objectives:
    - Build an intelligent chatbot for customer inquiries
    - Integrate with existing CRM system
    - Support multiple languages (English, Spanish, French)
    
    Technical Requirements:
    - REST API endpoints for chat integration
    - Machine learning model for intent classification
    - Database for conversation history
    - Real-time response capability (<2 seconds)
    
    Success Criteria:
    - 90% customer satisfaction rating
    - Handle 80% of inquiries without human escalation
    - Support 1000+ concurrent users
    
    Timeline: 3 months
    """
    
    return {
        "project_goals": sample_goals,
        "messages": [f"Human has set project goals: {sample_goals}"],
        "current_phase": "goal_setting_complete"
    }


async def cto(state: goals.State, config: RunnableConfig) -> Dict[str, Any]:
    """CTO creates work items and delegates to managers based on human-defined goals."""
    print("🔧 CTO: Creating work breakdown based on human-defined goals...")
    
    configuration = config.get("configurable", {})
    max_managers = configuration.get("max_managers", 3)
    
    # Create work items based on human goals
    project_goals = state.get("project_goals", "Default development tasks")
    
    work_items = [
        goals.WorkItem(
            id="work_1",
            title="Core Implementation",
            description=f"Implement core functionality for: {project_goals}",
            priority=3,
            created_by="cto"
        ),
        goals.WorkItem(
            id="work_2", 
            title="Integration Layer",
            description=f"Build integration components for: {project_goals}",
            priority=2,
            created_by="cto"
        ),
        goals.WorkItem(
            id="work_3",
            title="Testing Framework", 
            description=f"Develop comprehensive testing for: {project_goals}",
            priority=4,
            created_by="cto"
        ),
        goals.WorkItem(
            id="work_4",
            title="Documentation",
            description=f"Create documentation for: {project_goals}", 
            priority=1,
            created_by="cto"
        )
    ]
    
    # Create manager instances
    manager_ids = [f"manager_{i}" for i in range(max_managers)]
    print(f"   Created {len(manager_ids)} managers: {manager_ids}")
    
    return {
        "work_queue": work_items,
        "active_managers": manager_ids,
        "current_phase": "delegation"
    }


def should_continue_with_managers(state: goals.State) -> Literal["engineering_manager", "review"]:
    """Route to manager delegation or review phase."""
    if state.current_phase == "delegation" and state.active_managers:
        return "engineering_manager"
    return "review"


async def engineering_manager(state: goals.State, config: RunnableConfig) -> Dict[str, Any]:
    """Engineering Manager takes work and delegates to their team."""
    configuration = config.get("configurable", {})
    max_senior_engineers = configuration.get("max_senior_engineers_per_manager", 2)
    
    if not state.active_managers:
        print("   No active managers remaining")
        return {"current_phase": "execution"}
    
    # Process one manager at a time
    current_manager = state.active_managers[0]
    print(f"👔 Manager {current_manager}: Building team and delegating work...")
    
    # Create complete team structure for this manager
    # 1:1 relationship with QA engineer
    qa_engineer = f"{current_manager}_qa_engineer"
    
    # Orchestrator-worker pattern for senior engineers (parallelization with aggregation)
    senior_engineer_ids = [f"{current_manager}_senior_eng_{i}" for i in range(max_senior_engineers)]
    
    # Complete team for this manager
    team_members = [qa_engineer] + senior_engineer_ids
    
    print(f"   Created team structure:")
    print(f"     QA Engineer (1:1): {qa_engineer}")
    print(f"     Senior Engineers (orchestrator-worker): {senior_engineer_ids}")
    
    # Take work items from the queue
    available_work = [w for w in state.work_queue if w.status == "pending"]
    manager_work = available_work[:3] if available_work else []  # Take up to 3 work items per manager
    
    if manager_work:
        # Assign work based on role specialization
        for i, work_item in enumerate(manager_work):
            if i == 0 and len(manager_work) > 0:
                # First item goes to QA Engineer
                work_item.assigned_to = qa_engineer
                work_item.status = "assigned"
                print(f"   Assigned '{work_item.title}' to QA Engineer: {qa_engineer}")
            else:
                # Remaining items go to Senior Engineers (orchestrator-worker pattern)
                assigned_engineer = senior_engineer_ids[(i-1) % len(senior_engineer_ids)]
                work_item.assigned_to = assigned_engineer
                work_item.status = "assigned"
                print(f"   Assigned '{work_item.title}' to Senior Engineer: {assigned_engineer}")
        
        # Update state
        updated_work_queue = [w for w in state.work_queue if w not in manager_work] + manager_work
        updated_active_engineers = state.active_engineers.copy()
        updated_active_engineers[current_manager] = team_members
        
        # Remove this manager from active list (processed)
        remaining_managers = state.active_managers[1:]
        
        return {
            "work_queue": updated_work_queue,
            "active_managers": remaining_managers,
            "active_engineers": updated_active_engineers,
            "current_phase": "execution" if not remaining_managers else "delegation"
        }
    
    print("   No work available for manager")
    return {"current_phase": "execution"}


def should_continue_with_engineers(state: goals.State) -> Literal["senior_engineer", "senior_engineer_aggregator", "qa_engineer", "evaluation", "review"]:
    """Route to appropriate engineer type, aggregator, evaluation phase, or review phase."""
    assigned_work = [w for w in state.work_queue if w.status == "assigned"]
    evaluation_work = [w for w in state.evaluation_queue if w.status == "evaluation"]
    
    # Check if there's work in evaluation queue
    if evaluation_work:
        return "evaluation"
    
    if not assigned_work:
        return "review"
    
    # Check if we have multiple completed senior engineer work items that need aggregation
    completed_senior_work = [w for w in state.evaluation_queue if 
                            w.assigned_to and "senior_eng" in w.assigned_to and 
                            w.evaluation_loop and w.evaluation_loop.current_stage == "completed"]
    
    if len(completed_senior_work) > 1:
        return "senior_engineer_aggregator"
    
    # Check what type of engineer should work next
    senior_work = [w for w in assigned_work if w.assigned_to and "senior_eng" in w.assigned_to]
    qa_work = [w for w in assigned_work if w.assigned_to and "qa_engineer" in w.assigned_to]
    
    # Priority: Senior engineers work first (development), then QA tests
    if senior_work:
        return "senior_engineer"
    elif qa_work:
        return "qa_engineer"
    
    return "review"


def should_continue_with_evaluation(state: goals.State) -> Literal["unit_test_evaluator", "self_review_evaluator", "peer_review_evaluator", "integration_test_evaluator", "manager_review_evaluator", "cto_review_evaluator", "human_escalation_evaluator", "execution", "review"]:
    """Route to appropriate evaluation stage or back to execution."""
    
    # Check if there are any items in evaluation queue
    if not state.evaluation_queue:
        # Check if there's more work to be done
        assigned_work = [w for w in state.work_queue if w.status == "assigned"]
        return "execution" if assigned_work else "review"
    
    # Route based on current evaluation stage
    for work_item in state.evaluation_queue:
        stage = work_item.evaluation_loop.current_stage
        
        if stage == "unit_test":
            return "unit_test_evaluator"
        elif stage == "self_review":
            return "self_review_evaluator"
        elif stage == "peer_review":
            return "peer_review_evaluator"
        elif stage == "integration_test":
            return "integration_test_evaluator"
        elif stage == "manager_review":
            return "manager_review_evaluator"
        elif stage == "cto_review":
            return "cto_review_evaluator"
        elif stage == "human_escalation":
            return "human_escalation_evaluator"
    
    # Check if there's more work to be done
    assigned_work = [w for w in state.work_queue if w.status == "assigned"]
    return "execution" if assigned_work else "review"


async def qa_engineer(state: goals.State, config: RunnableConfig) -> Dict[str, Any]:
    """QA Engineer executes testing and quality assurance work."""
    
    # Get work items assigned to QA engineers
    qa_work = [w for w in state.work_queue if w.status == "assigned" and w.assigned_to and "qa_engineer" in w.assigned_to]
    
    if not qa_work:
        return {"current_phase": "execution"}
    
    # Process one QA work item at a time
    work_item = qa_work[0]
    engineer_id = work_item.assigned_to
    print(f"🧪 QA Engineer {engineer_id}: Testing '{work_item.title}'")
    
    # Mark work as completed
    work_item.status = "completed"
    work_item.result = f"QA testing completed for '{work_item.title}' by {engineer_id}"
    
    # Update work queue
    updated_work_queue = state.work_queue.copy()
    for i, w in enumerate(updated_work_queue):
        if w.id == work_item.id:
            updated_work_queue[i] = work_item
            break
    
    # Move to completed work
    completed_work = state.completed_work + [work_item]
    
    # Check if all work is done
    remaining_assigned = [w for w in updated_work_queue if w.status == "assigned"]
    next_phase = "review" if not remaining_assigned else "execution"
    
    return {
        "work_queue": updated_work_queue,
        "completed_work": completed_work,
        "current_phase": next_phase
    }


async def senior_engineer(state: goals.State, config: RunnableConfig) -> Dict[str, Any]:
    """Senior Engineer executes development work."""
    
    # Get work items assigned to senior engineers
    senior_work = [w for w in state.work_queue if w.status == "assigned" and w.assigned_to and "senior_eng" in w.assigned_to]
    
    if not senior_work:
        return {"current_phase": "execution"}
    
    # Process one senior engineer work item at a time
    work_item = senior_work[0]
    engineer_id = work_item.assigned_to
    print(f"� Senior Engineer {engineer_id}: Developing '{work_item.title}'")
    
    # Mark work as entering evaluation phase
    work_item.status = "evaluation"
    work_item.result = f"Development completed for '{work_item.title}' by {engineer_id}"
    
    # Initialize evaluation loop
    work_item.evaluation_loop = goals.EvaluationLoop()
    
    # Update work queue
    updated_work_queue = state.work_queue.copy()
    for i, w in enumerate(updated_work_queue):
        if w.id == work_item.id:
            updated_work_queue[i] = work_item
            break
    
    # Move to evaluation queue instead of completed work
    evaluation_queue = state.evaluation_queue + [work_item]
    
    # Check if all work is done
    remaining_assigned = [w for w in updated_work_queue if w.status == "assigned"]
    next_phase = "evaluation" if evaluation_queue else ("review" if not remaining_assigned else "execution")
    
    return {
        "work_queue": updated_work_queue,
        "evaluation_queue": evaluation_queue,
        "current_phase": next_phase
    }


# Now we need an aggregator for senior engineer outputs
async def senior_engineer_aggregator(state: goals.State, config: RunnableConfig) -> Dict[str, Any]:
    """Aggregates outputs from multiple senior engineers working in parallel on different tasks."""
    
    # Get completed development work from senior engineers that passed evaluation
    completed_senior_work = [w for w in state.evaluation_queue if 
                            w.assigned_to and "senior_eng" in w.assigned_to and 
                            w.evaluation_loop and w.evaluation_loop.current_stage == "completed"]
    
    if len(completed_senior_work) < 2:
        return {"current_phase": "execution"}
    
    print(f"🔗 Senior Engineer Aggregator: Combining {len(completed_senior_work)} parallel development outputs")
    
    # Combine multiple outputs into integrated deliverable for QA
    combined_results = []
    manager_prefix = None
    
    for work in completed_senior_work:
        combined_results.append(f"- {work.title}: {work.result}")
        # Extract manager prefix for QA assignment
        if not manager_prefix and work.assigned_to:
            manager_prefix = work.assigned_to.split('_senior_eng')[0]
    
    # Create new aggregated work item for QA evaluation
    aggregated_work = goals.WorkItem(
        id=f"integrated_output_{completed_senior_work[0].id}",
        title=f"Integrated Development Package",
        description=f"Combined deliverable from {len(completed_senior_work)} senior engineers working in parallel",
        priority=max(w.priority for w in completed_senior_work),
        created_by="senior_engineer_aggregator",
        assigned_to=f"{manager_prefix}_qa_engineer" if manager_prefix else "qa_engineer",
        status="assigned",
        result=f"Integrated Development Package:\n" + "\n".join(combined_results)
    )
    
    print(f"   Created integrated package: '{aggregated_work.title}'")
    print(f"   Assigned to QA Engineer: {aggregated_work.assigned_to}")
    
    # Update work queue: remove individual completed items, add aggregated item
    updated_work_queue = [w for w in state.work_queue if w not in completed_senior_work] + [aggregated_work]
    
    # Remove completed items from evaluation queue
    updated_evaluation_queue = [w for w in state.evaluation_queue if w not in completed_senior_work]
    
    return {
        "work_queue": updated_work_queue,
        "evaluation_queue": updated_evaluation_queue,
        "current_phase": "execution"  # Continue with QA testing of aggregated output
    }



# Evaluator-Optimizer Pattern Nodes
def unit_test_evaluator(state: goals.State) -> Dict[str, Any]:
    """Unit test evaluation stage"""
    print("\n🧪 Unit Test Evaluator")
    
    updated_evaluation_queue = []
    
    for work_item in state.evaluation_queue:
        if work_item.evaluation_loop.current_stage == "unit_test":
            print(f"  Running unit tests for: {work_item.title}")
            
            # Simulate unit test evaluation
            feedback = "Unit tests passing with 85% coverage. Consider adding edge case tests for error handling."
            work_item.evaluation_loop.feedback.append({
                "stage": "unit_test", 
                "feedback": feedback,
                "evaluator": "unit_test_evaluator"
            })
            
            # Move to next stage or increment loop
            if work_item.evaluation_loop.loop_count >= work_item.evaluation_loop.max_loops:
                work_item.evaluation_loop.current_stage = "self_review"
                work_item.evaluation_loop.loop_count = 1
            else:
                work_item.evaluation_loop.loop_count += 1
                work_item.status = "in_progress"  # Back to development
        
        updated_evaluation_queue.append(work_item)
    
    return {"evaluation_queue": updated_evaluation_queue}

def self_review_evaluator(state: goals.State) -> Dict[str, Any]:
    """Self review evaluation stage"""
    print("\n🔍 Self Review Evaluator")
    
    updated_evaluation_queue = []
    
    for work_item in state.evaluation_queue:
        if work_item.evaluation_loop.current_stage == "self_review":
            print(f"  Self reviewing: {work_item.title}")
            
            feedback = "Code structure looks good. Refactored error handling and improved documentation."
            work_item.evaluation_loop.feedback.append({
                "stage": "self_review", 
                "feedback": feedback,
                "evaluator": "self_review_evaluator"
            })
            
            # Move to next stage or increment loop
            if work_item.evaluation_loop.loop_count >= work_item.evaluation_loop.max_loops:
                work_item.evaluation_loop.current_stage = "peer_review"
                work_item.evaluation_loop.loop_count = 1
            else:
                work_item.evaluation_loop.loop_count += 1
                work_item.evaluation_loop.current_stage = "unit_test"  # Back to testing
        
        updated_evaluation_queue.append(work_item)

    return {"evaluation_queue": updated_evaluation_queue}

def peer_review_evaluator(state: goals.State) -> Dict[str, Any]:
    """Peer review evaluation stage"""
    print("\n👥 Peer Review Evaluator")
    
    updated_evaluation_queue = []
    
    for work_item in state.evaluation_queue:
        if work_item.evaluation_loop.current_stage == "peer_review":
            print(f"  Peer reviewing: {work_item.title}")
            
            feedback = "Good implementation. Suggested improvements to variable naming and added performance considerations."
            work_item.evaluation_loop.feedback.append({
                "stage": "peer_review", 
                "feedback": feedback,
                "evaluator": "peer_review_evaluator"
            })
            
            # Move to next stage or increment loop
            if work_item.evaluation_loop.loop_count >= work_item.evaluation_loop.max_loops:
                work_item.evaluation_loop.current_stage = "integration_test"
                work_item.evaluation_loop.loop_count = 1
            else:
                work_item.evaluation_loop.loop_count += 1
                work_item.evaluation_loop.current_stage = "unit_test"  # Back to start
        
        updated_evaluation_queue.append(work_item)

    return {"evaluation_queue": updated_evaluation_queue}

def integration_test_evaluator(state: goals.State) -> Dict[str, Any]:
    """Integration test evaluation stage"""
    print("\n🔗 Integration Test Evaluator")
    
    updated_evaluation_queue = []
    updated_completed_work = state.completed_work.copy()
    
    for work_item in state.evaluation_queue:
        if work_item.evaluation_loop.current_stage == "integration_test":
            print(f"  Integration testing: {work_item.title}")
            
            feedback = "Integration tests pass. API endpoints working correctly with external services."
            work_item.evaluation_loop.feedback.append({
                "stage": "integration_test", 
                "feedback": feedback,
                "evaluator": "integration_test_evaluator"
            })
            
            # Check if we need to escalate or can complete
            if work_item.evaluation_loop.escalation_count >= work_item.evaluation_loop.max_escalations:
                work_item.status = "completed"
                work_item.evaluation_loop.current_stage = "completed"
                updated_completed_work.append(work_item)
                # Don't add to updated_evaluation_queue (remove from evaluation)
            else:
                work_item.evaluation_loop.current_stage = "manager_review"
                updated_evaluation_queue.append(work_item)
        else:
            updated_evaluation_queue.append(work_item)

    return {
        "evaluation_queue": updated_evaluation_queue,
        "completed_work": updated_completed_work
    }

def manager_review_evaluator(state: goals.State) -> Dict[str, Any]:
    """Manager review evaluation stage (escalation)"""
    print("\n👔 Manager Review Evaluator")
    
    updated_evaluation_queue = []
    
    for work_item in state.evaluation_queue:
        if work_item.evaluation_loop.current_stage == "manager_review":
            print(f"  Manager reviewing: {work_item.title}")
            
            feedback = "Meets business requirements. Approved for deployment to staging environment."
            work_item.evaluation_loop.feedback.append({
                "stage": "manager_review", 
                "feedback": feedback,
                "evaluator": "manager_review_evaluator"
            })
            
            # Move to next escalation stage
            work_item.evaluation_loop.current_stage = "cto_review"
        
        updated_evaluation_queue.append(work_item)

    return {"evaluation_queue": updated_evaluation_queue}

def cto_review_evaluator(state: goals.State) -> Dict[str, Any]:
    """CTO review evaluation stage (final escalation before human)"""
    print("\n🏛️ CTO Review Evaluator")
    
    updated_evaluation_queue = []
    updated_failed_work = state.failed_work.copy()
    
    for work_item in state.evaluation_queue:
        if work_item.evaluation_loop.current_stage == "cto_review":
            print(f"  CTO reviewing: {work_item.title}")
            
            feedback = "Strategic alignment confirmed. Approved for production deployment."
            work_item.evaluation_loop.feedback.append({
                "stage": "cto_review", 
                "feedback": feedback,
                "evaluator": "cto_review_evaluator"
            })
            
            # Check if we need to escalate to human or can complete
            if work_item.evaluation_loop.escalation_count >= work_item.evaluation_loop.max_escalations:
                # Escalate to human for final decision
                work_item.evaluation_loop.current_stage = "human_escalation"
                updated_evaluation_queue.append(work_item)
            else:
                # Restart the evaluation cycle with escalation
                work_item.evaluation_loop.escalation_count += 1
                work_item.evaluation_loop.current_stage = "unit_test"
                work_item.evaluation_loop.loop_count = 1
                updated_evaluation_queue.append(work_item)
        else:
            updated_evaluation_queue.append(work_item)

    return {
        "evaluation_queue": updated_evaluation_queue,
        "failed_work": updated_failed_work
    }


def human_escalation_evaluator(state: goals.State) -> Dict[str, Any]:
    """Human escalation when all automated evaluation loops fail"""
    print("\n👤 Human Escalation: Critical review required")
    
    updated_evaluation_queue = []
    updated_completed_work = state.completed_work.copy()
    updated_failed_work = state.failed_work.copy()
    
    for work_item in state.evaluation_queue:
        if work_item.evaluation_loop.current_stage == "human_escalation":
            print(f"  Human reviewing critical item: {work_item.title}")
            
            # Gather all feedback for human review
            feedback_summary = "\n".join([
                f"- {fb['stage']}: {fb['feedback']}" 
                for fb in work_item.evaluation_loop.feedback
            ])
            
            # For demo purposes, simulate human decision-making
            # In LangGraph Studio, this would present an interactive decision interface
            print(f"  Critical escalation for: {work_item.title}")
            print(f"  Feedback summary: {feedback_summary}")
            
            # Demo human decision (in production, this would be actual human input)
            decision = "approve"  # Could be "approve", "reject", or "redirect"
            human_feedback = "After careful review, work meets requirements"
            
            # Record human decision
            work_item.evaluation_loop.feedback.append({
                "stage": "human_escalation",
                "feedback": f"Human decision: {decision} - {human_feedback}",
                "evaluator": "human_escalation_evaluator"
            })
            
            if decision == "approve":
                work_item.status = "completed"
                work_item.evaluation_loop.current_stage = "completed"
                updated_completed_work.append(work_item)
                print(f"   ✅ Human approved: {work_item.title}")
            elif decision == "redirect":
                # Restart with human guidance
                work_item.evaluation_loop.escalation_count = 0
                work_item.evaluation_loop.current_stage = "unit_test"
                work_item.evaluation_loop.loop_count = 1
                work_item.status = "in_progress"
                updated_evaluation_queue.append(work_item)
                print(f"   🔄 Human redirected: {work_item.title}")
            else:  # reject
                work_item.status = "failed"
                work_item.evaluation_loop.current_stage = "failed"
                updated_failed_work.append(work_item)
                print(f"   ❌ Human rejected: {work_item.title}")
        else:
            updated_evaluation_queue.append(work_item)

    return {
        "evaluation_queue": updated_evaluation_queue,
        "completed_work": updated_completed_work,
        "failed_work": updated_failed_work
    }


async def review(state: goals.State, config: RunnableConfig) -> Dict[str, Any]:
    """Review completed work and organizational structure."""
    print("📊 Review: Organizational structure summary...")
    
    completed_count = len(state.completed_work)
    total_managers = len(state.active_engineers)
    
    print(f"   ✅ Work items completed: {completed_count}")
    print(f"   👔 Managers created: {total_managers}")
    
    # Show detailed org structure by role
    total_qa = 0
    total_senior = 0
    
    for manager_id, team_members in state.active_engineers.items():
        print(f"\n   🏢 {manager_id} team structure:")
        
        qa_engineers = [e for e in team_members if "qa_engineer" in e]
        senior_engineers = [e for e in team_members if "senior_eng" in e]
        
        total_qa += len(qa_engineers)
        total_senior += len(senior_engineers)
        
        print(f"     🧪 QA Engineer (1:1): {qa_engineers[0] if qa_engineers else 'None'}")
        print(f"     � Senior Engineers (orchestrator-worker): {senior_engineers}")
    
    print(f"\n   📈 Total team composition:")
    print(f"     QA Engineers: {total_qa}")
    print(f"     Senior Engineers: {total_senior}")
    print(f"     Total Engineers: {total_qa + total_senior}")
    
    return {
        "current_phase": "completed"
    }

# Define the graph with proper organizational structure, evaluation pipeline, and human-in-the-loop
graph = (
    StateGraph(goals.State, config_schema=Configuration)
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
