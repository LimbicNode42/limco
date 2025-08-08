"""Organizational agents for the development team workflow.

Contains human-in-the-loop functions and organizational role implementations:
- Human goal setting and escalation
- CTO orchestration and work breakdown
- Engineering manager delegation
- Senior engineer development
- QA engineer testing
- Senior engineer aggregation
"""

from __future__ import annotations

from typing import Any, Dict
from langchain_core.runnables import RunnableConfig
import states


def human_goal_setting(state: states.State, config: RunnableConfig) -> Dict[str, Any]:
    """Human sets project goals at the beginning of the workflow.
    
    This function serves as the human-in-the-loop entry point for goal setting.
    In LangGraph Studio, this would present an interactive form for goal input.
    """
    print("🚀 Human Goal Setting Stage")
    print("=" * 50)
    print("Awaiting human input for project states...")
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


async def cto(state: states.State, config: RunnableConfig) -> Dict[str, Any]:
    """CTO creates work items and delegates to managers based on human-defined states."""
    print("🔧 CTO: Creating work breakdown based on human-defined states...")
    
    configuration = config.get("configurable", {})
    max_managers = configuration.get("max_managers", 3)
    
    # Create work items based on human goals
    project_goals = state.get("project_goals", "Default development tasks")
    
    work_items = [
        states.WorkItem(
            id="work_1",
            title="Core Implementation",
            description=f"Implement core functionality for: {project_goals}",
            priority=3,
            created_by="cto"
        ),
        states.WorkItem(
            id="work_2", 
            title="Integration Layer",
            description=f"Build integration components for: {project_goals}",
            priority=2,
            created_by="cto"
        ),
        states.WorkItem(
            id="work_3",
            title="Testing Framework", 
            description=f"Develop comprehensive testing for: {project_goals}",
            priority=4,
            created_by="cto"
        ),
        states.WorkItem(
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


async def engineering_manager(state: states.State, config: RunnableConfig) -> Dict[str, Any]:
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


async def senior_engineer(state: states.State, config: RunnableConfig) -> Dict[str, Any]:
    """Senior Engineer executes development work."""
    
    # Get work items assigned to senior engineers
    senior_work = [w for w in state.work_queue if w.status == "assigned" and w.assigned_to and "senior_eng" in w.assigned_to]
    
    if not senior_work:
        return {"current_phase": "execution"}
    
    # Process one senior engineer work item at a time
    work_item = senior_work[0]
    engineer_id = work_item.assigned_to
    print(f"👨‍💻 Senior Engineer {engineer_id}: Developing '{work_item.title}'")
    
    # Mark work as entering evaluation phase
    work_item.status = "evaluation"
    work_item.result = f"Development completed for '{work_item.title}' by {engineer_id}"
    
    # Initialize evaluation loop
    work_item.evaluation_loop = states.EvaluationLoop()
    
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


async def qa_engineer(state: states.State, config: RunnableConfig) -> Dict[str, Any]:
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


async def senior_engineer_aggregator(state: states.State, config: RunnableConfig) -> Dict[str, Any]:
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
    aggregated_work = states.WorkItem(
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


async def review(state: states.State, config: RunnableConfig) -> Dict[str, Any]:
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
        print(f"     👨‍💻 Senior Engineers (orchestrator-worker): {senior_engineers}")
    
    print(f"\n   📈 Total team composition:")
    print(f"     QA Engineers: {total_qa}")
    print(f"     Senior Engineers: {total_senior}")
    print(f"     Total Engineers: {total_qa + total_senior}")
    
    return {
        "current_phase": "completed"
    }
