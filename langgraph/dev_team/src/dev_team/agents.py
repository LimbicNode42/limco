"""LLM-powered agent implementations with model integration.

Enhanced agents that use appropriate LLMs with rate limiting and fallbacks:
- Technical agents use Claude 4 Sonnet for precision
- Non-technical agents use Gemini 2.5 Flash for efficiency
- All agents have fallback models and rate limiting
"""

from __future__ import annotations

from typing import Any, Dict
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, SystemMessage
import states
from models import get_model_for_agent
from tools import get_all_tools


async def llm_human_goal_setting(state: states.State, config: RunnableConfig) -> Dict[str, Any]:
    """LLM-powered human goal setting with structured project planning."""
    print("🚀 LLM Human Goal Setting Stage")
    print("=" * 50)
    
    # This is still human-in-the-loop, but we can use LLM to structure/validate input
    model = get_model_for_agent("human_goal_setting")
    
    # In real implementation, human would provide input
    # For demo, we'll use LLM to generate well-structured goals
    system_prompt = """You are a product manager helping to structure project goals. 
    Create comprehensive, well-structured project goals including:
    - Clear objectives
    - Technical requirements
    - Success criteria
    - Timeline considerations
    
    Focus on an AI-powered customer support system project."""
    
    human_input = "I need to create goals for an AI customer support chatbot project."
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_input)
    ]
    
    try:
        response = await model.ainvoke(messages)
        project_goals = response.content
        
        print(f"Generated structured project goals")
        
        return {
            "project_goals": project_goals,
            "messages": [f"Human (with LLM assistance) has set project goals: {project_goals}"],
            "current_phase": "goal_setting_complete"
        }
    except Exception as e:
        print(f"Error in LLM goal setting: {e}")
        # Fallback to original implementation
        return {
            "project_goals": "AI-Powered Customer Support System with basic chatbot functionality",
            "messages": ["Fallback: Basic project goals set"],
            "current_phase": "goal_setting_complete"
        }


async def llm_cto(state: states.State, config: RunnableConfig) -> Dict[str, Any]:
    """LLM-powered CTO for strategic planning and work breakdown."""
    print("👔 LLM CTO: Strategic Planning & Architecture")
    print("=" * 50)
    
    model = get_model_for_agent("cto")
    tools = get_all_tools()
    
    # Bind tools to model for potential handoffs
    model_with_tools = model.bind_tools(tools)
    
    configuration = config.get("configurable", {})
    max_managers = configuration.get("max_managers", 3)
    
    project_goals = state.get("project_goals", "No specific goals provided")
    
    system_prompt = f"""You are a CTO responsible for strategic planning and work breakdown.

    Your responsibilities:
    - Analyze project requirements and create strategic plans
    - Break down work into manageable components
    - Create technical architecture decisions
    - Delegate work to engineering managers
    - Make escalation decisions when needed

    You have access to handoff tools to delegate work or escalate decisions.
    You need to create {max_managers} manager assignments.

    Current project goals: {project_goals}
    
    Provide a strategic analysis and create specific work items for the engineering team."""
    
    human_message = f"""Please analyze these project goals and create a strategic plan with work breakdown:

    {project_goals}

    Create {max_managers} distinct work areas that can be managed by different engineering managers."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message)
    ]
    
    try:
        response = await model_with_tools.ainvoke(messages)
        strategic_analysis = response.content
        
        # Create work items based on LLM analysis
        work_items = [
            states.WorkItem(
                id="work_1",
                title="Core AI/ML Implementation", 
                description=f"Implement core AI functionality based on strategic analysis: {strategic_analysis[:200]}...",
                priority=3,
                created_by="llm_cto"
            ),
            states.WorkItem(
                id="work_2",
                title="Integration & API Layer",
                description=f"Build integration components as per strategic plan: {strategic_analysis[200:400]}...",
                priority=2,
                created_by="llm_cto"
            ),
            states.WorkItem(
                id="work_3", 
                title="Testing & Quality Framework",
                description=f"Comprehensive testing strategy: {strategic_analysis[400:600]}...",
                priority=4,
                created_by="llm_cto"
            ),
            states.WorkItem(
                id="work_4",
                title="Documentation & Deployment",
                description=f"Documentation and deployment pipeline: {strategic_analysis[600:800]}...",
                priority=1,
                created_by="llm_cto"
            )
        ]
        
        manager_ids = [f"manager_{i}" for i in range(max_managers)]
        print(f"   LLM CTO created strategic plan and {len(manager_ids)} manager assignments")
        
        return {
            "work_queue": work_items,
            "active_managers": manager_ids,
            "strategic_analysis": strategic_analysis,
            "current_phase": "delegation",
            "messages": state.get("messages", []) + [f"CTO strategic analysis: {strategic_analysis[:200]}..."]
        }
        
    except Exception as e:
        print(f"Error in LLM CTO: {e}")
        # Fallback to basic work items
        return {
            "work_queue": [
                states.WorkItem(id="work_1", title="Basic Development", description="Basic development work", priority=2, created_by="cto_fallback")
            ],
            "active_managers": ["manager_0"],
            "current_phase": "delegation"
        }


async def llm_engineering_manager(state: states.State, config: RunnableConfig) -> Dict[str, Any]:
    """LLM-powered Engineering Manager for team coordination and task delegation."""
    print("👨‍💼 LLM Engineering Manager: Team Coordination")
    print("=" * 50)
    
    model = get_model_for_agent("engineering_manager")
    tools = get_all_tools()
    model_with_tools = model.bind_tools(tools)
    
    configuration = config.get("configurable", {})
    max_senior_engineers = configuration.get("max_senior_engineers_per_manager", 2)
    
    if not state.get("active_managers", []):
        return {"current_phase": "execution"}
    
    current_manager = state.get("active_managers", [])[0]
    available_work = [w for w in state.get("work_queue", []) if w.status == "pending"]
    
    if not available_work:
        return {"current_phase": "execution"}
    
    system_prompt = f"""You are an Engineering Manager responsible for team building and work delegation.

    Your responsibilities:
    - Build balanced engineering teams
    - Delegate work based on engineer specializations
    - Coordinate between team members
    - Ensure work is properly distributed
    - Use handoff tools to assign work to specific engineers

    You can create teams with:
    - 1 QA Engineer (for testing and quality assurance)
    - {max_senior_engineers} Senior Engineers (for development work)

    Available work items: {[w.title for w in available_work]}
    Current manager: {current_manager}

    Analyze the work and create appropriate team assignments."""
    
    work_descriptions = "\n".join([f"- {w.title}: {w.description}" for w in available_work[:3]])
    
    human_message = f"""Please analyze this work and create team assignments:

    {work_descriptions}

    Create a team structure and assign work appropriately between QA and Senior Engineers."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message)
    ]
    
    try:
        response = await model_with_tools.ainvoke(messages)
        delegation_plan = response.content
        
        # Create team structure
        qa_engineer = f"{current_manager}_qa_engineer"
        senior_engineer_ids = [f"{current_manager}_senior_eng_{i}" for i in range(max_senior_engineers)]
        team_members = [qa_engineer] + senior_engineer_ids
        
        # Assign work based on LLM recommendations
        manager_work = available_work[:3]
        for i, work_item in enumerate(manager_work):
            if i == 0:
                # First item to QA Engineer
                work_item.assigned_to = qa_engineer
                work_item.status = "assigned"
                print(f"   LLM assigned '{work_item.title}' to QA Engineer: {qa_engineer}")
            else:
                # Remaining to Senior Engineers
                assigned_engineer = senior_engineer_ids[(i-1) % len(senior_engineer_ids)]
                work_item.assigned_to = assigned_engineer
                work_item.status = "assigned"
                print(f"   LLM assigned '{work_item.title}' to Senior Engineer: {assigned_engineer}")
        
        updated_work_queue = [w for w in state.get("work_queue", []) if w not in manager_work] + manager_work
        updated_active_engineers = state.get("active_engineers", {}).copy()
        updated_active_engineers[current_manager] = team_members
        remaining_managers = state.get("active_managers", [])[1:]
        
        return {
            "work_queue": updated_work_queue,
            "active_managers": remaining_managers,
            "active_engineers": updated_active_engineers,
            "delegation_plan": delegation_plan,
            "current_phase": "execution" if not remaining_managers else "delegation",
            "messages": state.get("messages", []) + [f"Engineering Manager delegation: {delegation_plan[:200]}..."]
        }
        
    except Exception as e:
        print(f"Error in LLM Engineering Manager: {e}")
        return {"current_phase": "execution"}


async def llm_senior_engineer(state: states.State, config: RunnableConfig) -> Dict[str, Any]:
    """LLM-powered Senior Engineer for development work."""
    print("👨‍💻 LLM Senior Engineer: Development Work")
    print("=" * 50)
    
    model = get_model_for_agent("senior_engineer")
    tools = get_all_tools()
    model_with_tools = model.bind_tools(tools)
    
    # Get work items assigned to senior engineers
    senior_work = [w for w in state.get("work_queue", []) if w.status == "assigned" and w.assigned_to and "senior_eng" in w.assigned_to]
    
    if not senior_work:
        return {"current_phase": "execution"}
    
    work_item = senior_work[0]
    engineer_id = work_item.assigned_to
    
    system_prompt = f"""You are a Senior Software Engineer responsible for development work.

    Your responsibilities:
    - Analyze technical requirements
    - Design and implement solutions
    - Write high-quality code
    - Ensure proper testing coverage
    - Use handoff tools when work is ready for QA or needs peer review

    Current assignment: {work_item.title}
    Description: {work_item.description}
    Engineer ID: {engineer_id}

    Provide a detailed technical implementation plan and mark work for evaluation."""
    
    human_message = f"""Please analyze and implement this development task:

    Task: {work_item.title}
    Requirements: {work_item.description}

    Provide your technical approach and implementation details."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message)
    ]
    
    try:
        response = await model_with_tools.ainvoke(messages)
        implementation_details = response.content
        
        print(f"   LLM Senior Engineer {engineer_id} completed: {work_item.title}")
        
        # Mark work as entering evaluation
        work_item.status = "evaluation"
        work_item.result = f"Development completed by {engineer_id}: {implementation_details}"
        work_item.evaluation_loop = states.EvaluationLoop()
        
        updated_work_queue = state.get("work_queue", []).copy()
        for i, w in enumerate(updated_work_queue):
            if w.id == work_item.id:
                updated_work_queue[i] = work_item
                break
        
        evaluation_queue = state.get("evaluation_queue", []) + [work_item]
        remaining_assigned = [w for w in updated_work_queue if w.status == "assigned"]
        next_phase = "evaluation" if evaluation_queue else ("review" if not remaining_assigned else "execution")
        
        return {
            "work_queue": updated_work_queue,
            "evaluation_queue": evaluation_queue,
            "implementation_details": implementation_details,
            "current_phase": next_phase,
            "messages": state.get("messages", []) + [f"Senior Engineer {engineer_id}: {implementation_details[:200]}..."]
        }
        
    except Exception as e:
        print(f"Error in LLM Senior Engineer: {e}")
        return {"current_phase": "execution"}


async def llm_qa_engineer(state: states.State, config: RunnableConfig) -> Dict[str, Any]:
    """LLM-powered QA Engineer for testing and quality assurance."""
    print("🧪 LLM QA Engineer: Quality Assurance")
    print("=" * 50)
    
    model = get_model_for_agent("qa_engineer")
    tools = get_all_tools()
    model_with_tools = model.bind_tools(tools)
    
    # Get work items assigned to QA engineers
    qa_work = [w for w in state.get("work_queue", []) if w.status == "assigned" and w.assigned_to and "qa_engineer" in w.assigned_to]
    
    if not qa_work:
        return {"current_phase": "execution"}
    
    work_item = qa_work[0]
    engineer_id = work_item.assigned_to
    
    system_prompt = f"""You are a QA Engineer responsible for comprehensive testing and quality assurance.

    Your responsibilities:
    - Design comprehensive test strategies
    - Execute various types of testing (unit, integration, system, acceptance)
    - Identify quality issues and bugs
    - Ensure code meets quality standards
    - Use handoff tools to return work or escalate issues

    Current assignment: {work_item.title}
    Description: {work_item.description}
    QA Engineer ID: {engineer_id}

    Provide detailed testing results and quality assessment."""
    
    human_message = f"""Please perform comprehensive QA testing on this work:

    Task: {work_item.title}
    Requirements: {work_item.description}

    Provide your testing strategy, execution results, and quality assessment."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message)
    ]
    
    try:
        response = await model_with_tools.ainvoke(messages)
        qa_results = response.content
        
        print(f"   LLM QA Engineer {engineer_id} tested: {work_item.title}")
        
        # Mark work as completed
        work_item.status = "completed"
        work_item.result = f"QA testing completed by {engineer_id}: {qa_results}"
        
        updated_work_queue = state.get("work_queue", []).copy()
        for i, w in enumerate(updated_work_queue):
            if w.id == work_item.id:
                updated_work_queue[i] = work_item
                break
        
        completed_work = state.get("completed_work", []) + [work_item]
        remaining_assigned = [w for w in updated_work_queue if w.status == "assigned"]
        next_phase = "review" if not remaining_assigned else "execution"
        
        return {
            "work_queue": updated_work_queue,
            "completed_work": completed_work,
            "qa_results": qa_results,
            "current_phase": next_phase,
            "messages": state.get("messages", []) + [f"QA Engineer {engineer_id}: {qa_results[:200]}..."]
        }
        
    except Exception as e:
        print(f"Error in LLM QA Engineer: {e}")
        return {"current_phase": "execution"}


async def llm_senior_engineer_aggregator(state: states.State, config: RunnableConfig) -> Dict[str, Any]:
    """Aggregates outputs from multiple senior engineers working in parallel on different tasks."""
    
    # Get completed development work from senior engineers that passed evaluation
    completed_senior_work = [w for w in state.get("evaluation_queue", []) if 
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
    updated_work_queue = [w for w in state.get("work_queue", []) if w not in completed_senior_work] + [aggregated_work]
    
    # Remove completed items from evaluation queue
    updated_evaluation_queue = [w for w in state.get("evaluation_queue", []) if w not in completed_senior_work]
    
    return {
        "work_queue": updated_work_queue,
        "evaluation_queue": updated_evaluation_queue,
        "current_phase": "execution"  # Continue with QA testing of aggregated output
    }


async def llm_review(state: states.State, config: RunnableConfig) -> Dict[str, Any]:
    """LLM-powered final review and summary."""
    print("📊 LLM Review: Final Analysis")
    print("=" * 50)
    
    model = get_model_for_agent("review")
    
    completed_count = len(state.get("completed_work", []))
    total_managers = len(state.get("active_engineers", {}))
    
    system_prompt = """You are conducting a final project review and organizational analysis.

    Your responsibilities:
    - Analyze project completion status
    - Assess team performance and structure
    - Provide insights and recommendations
    - Summarize key achievements and areas for improvement

    Provide a comprehensive project review with actionable insights."""
    
    # Gather project information
    project_summary = f"""
    Project Completion Summary:
    - Completed work items: {completed_count}
    - Total managers created: {total_managers}
    - Team structure: {total_managers} management teams with QA and Senior Engineers
    
    Recent messages: {state.get('messages', [])[-5:] if state.get('messages') else 'No recent messages'}
    """
    
    human_message = f"""Please provide a comprehensive review of this project:

    {project_summary}

    Analyze the organizational structure, work completion, and provide recommendations."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message)
    ]
    
    try:
        response = await model.ainvoke(messages)
        review_analysis = response.content
        
        print(f"   LLM Review completed with strategic insights")
        
        return {
            "review_analysis": review_analysis,
            "current_phase": "completed",
            "messages": state.get("messages", []) + [f"Final review: {review_analysis[:200]}..."]
        }
        
    except Exception as e:
        print(f"Error in LLM Review: {e}")
        # Fallback to basic review
        return {
            "review_analysis": f"Project completed: {completed_count} items, {total_managers} teams",
            "current_phase": "completed"
        }
