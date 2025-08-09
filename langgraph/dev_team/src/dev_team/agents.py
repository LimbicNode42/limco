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


def safe_get_state_attr(state: states.State, key: str, default=None):
    """Safely get state attribute whether state is dict-like or object-like."""
    if hasattr(state, 'get'):
        return state.get(key, default)
    return getattr(state, key, default)


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
    """LLM-powered CTO for strategic planning, complexity analysis, and dynamic team sizing."""
    print("🎯 LLM CTO: Strategic Planning & Dynamic Team Sizing")
    print("=" * 60)
    
    model = get_model_for_agent("cto")
    tools = get_all_tools()
    model_with_tools = model.bind_tools(tools)
    
    # Import complexity analyzer
    from complexity_analyzer import assess_project_complexity, create_iteration_manager
    
    project_goals = safe_get_state_attr(state, "project_goals", "No goals specified")
    existing_work_context = ""
    work_queue = safe_get_state_attr(state, "work_queue", [])
    if work_queue:
        existing_work_context = f"Existing work context: {len(work_queue)} items in queue"
    
    print(f"   📊 Analyzing project complexity for: {project_goals[:100]}...")
    
    # Perform complexity analysis
    try:
        complexity_assessment = await assess_project_complexity(
            project_goals=project_goals,
            work_context=existing_work_context,
            config=config
        )
        
        print(f"   🧠 Complexity Analysis Complete:")
        print(f"      Overall Score: {complexity_assessment.overall_score:.1f}/10.0")
        print(f"      Recommended Managers: {complexity_assessment.recommended_managers}")
        print(f"      Engineers per Manager: {complexity_assessment.recommended_engineers_per_manager}")
        print(f"      Total Workers: {complexity_assessment.total_recommended_workers}")
        
        # Update team structure in state
        team_structure = states.ComplexityBasedTeamStructure(
            recommended_managers=complexity_assessment.recommended_managers,
            recommended_engineers_per_manager=complexity_assessment.recommended_engineers_per_manager,
            total_recommended_workers=complexity_assessment.total_recommended_workers,
            complexity_score=complexity_assessment.overall_score,
            requires_iteration=complexity_assessment.requires_iteration,
            iteration_strategy=complexity_assessment.iteration_strategy,
            analysis_reasoning=complexity_assessment.reasoning
        )
        
    except Exception as e:
        print(f"   ⚠️  Complexity analysis failed, using defaults: {e}")
        # Fallback to conservative defaults
        team_structure = states.ComplexityBasedTeamStructure(
            recommended_managers=1,
            recommended_engineers_per_manager=2,
            total_recommended_workers=3,
            complexity_score=5.0,
            analysis_reasoning="Fallback due to analysis error"
        )
    
    # Create strategic plan with complexity insights
    system_prompt = f"""You are a Chief Technology Officer responsible for strategic planning and work breakdown.

    Your responsibilities:
    - Analyze project objectives and create strategic direction
    - Break down high-level goals into specific work items  
    - Consider technical complexity and resource requirements
    - Plan optimal team structure based on complexity analysis
    - Create clear, actionable work packages

    COMPLEXITY ANALYSIS RESULTS:
    - Overall Complexity: {team_structure.complexity_score:.1f}/10.0
    - Recommended Team Size: {team_structure.total_recommended_workers} workers
    - Team Structure: {team_structure.recommended_managers} managers, {team_structure.recommended_engineers_per_manager} engineers each
    - Reasoning: {team_structure.analysis_reasoning}
    
    Use this analysis to inform your strategic planning and work breakdown.
    Create work items that align with the recommended team structure.
    """
    
    human_message = f"""Please create a strategic plan and work breakdown for this project:

PROJECT GOALS: {project_goals}

Based on the complexity analysis, create {3 + team_structure.recommended_managers} strategic work items that can be effectively handled by the recommended team structure of {team_structure.total_recommended_workers} workers.

Focus on work items that:
1. Align with the complexity assessment
2. Can be distributed across {team_structure.recommended_managers} management teams  
3. Leverage the strengths of {team_structure.recommended_engineers_per_manager} engineers per team
4. Account for the overall complexity score of {team_structure.complexity_score:.1f}/10.0"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message)
    ]
    
    try:
        response = await model_with_tools.ainvoke(messages)
        strategic_analysis = response.content
        
        print(f"   📋 Strategic Analysis Generated:")
        print(f"      Length: {len(strategic_analysis)} characters")
        
        # Create work items based on complexity and team structure
        base_work_count = 3 + team_structure.recommended_managers
        
        work_items = []
        for i in range(base_work_count):
            # Vary priority based on complexity and position
            if team_structure.complexity_score >= 8.0:
                priority = 5 if i == 0 else (4 if i == 1 else 3)
            elif team_structure.complexity_score >= 6.0:
                priority = 4 if i == 0 else (3 if i == 1 else 2)  
            else:
                priority = 3 if i == 0 else 2
            
            work_item = states.WorkItem(
                id=f"work_{i+1}",
                title=f"Strategic Component #{i+1}",
                description=f"Work package based on strategic analysis: {strategic_analysis[i*200:(i+1)*200]}...",
                priority=priority,
                created_by="llm_cto",
                iteration_batch=0  # Start with iteration 0
            )
            work_items.append(work_item)
        
        # Setup iteration state if needed
        iteration_state = states.IterationState()
        if team_structure.requires_iteration:
            print(f"   🔄 Setting up iteration strategy: {team_structure.iteration_strategy}")
            iteration_manager = create_iteration_manager()
            
            # Plan iterations based on work items and team constraints
            configuration = config.get("configurable", {})
            from complexity_analyzer import ResourceLimits
            limits = ResourceLimits(
                max_managers=configuration.get("max_managers", 3),
                max_engineers_per_manager=configuration.get("max_engineers_per_manager", 3), 
                max_total_workers=configuration.get("max_total_workers", 9)
            )
            
            work_batches = iteration_manager.plan_iterations(work_items, limits, team_structure.total_recommended_workers)
            
            # Update work items with iteration batch numbers
            for batch_idx, batch in enumerate(work_batches):
                for work_item in batch:
                    work_item.iteration_batch = batch_idx
            
            iteration_state = states.IterationState(
                is_iterative=True,
                current_iteration=0,
                total_iterations=len(work_batches),
                iteration_work_batches=[[w.id for w in batch] for batch in work_batches]
            )
        
        # Create manager assignments based on team structure
        manager_ids = [f"manager_{i}" for i in range(team_structure.recommended_managers)]
        
        print(f"   👥 Team Structure Created:")
        print(f"      Managers: {len(manager_ids)} ({', '.join(manager_ids)})")
        print(f"      Engineers per Manager: {team_structure.recommended_engineers_per_manager}")
        print(f"      Iteration Planning: {'Yes' if iteration_state.is_iterative else 'No'}")
        if iteration_state.is_iterative:
            print(f"      Total Iterations: {iteration_state.total_iterations}")
        
        return {
            "work_queue": work_items,
            "active_managers": manager_ids,
            "team_structure": team_structure,
            "iteration_state": iteration_state,
            "strategic_analysis": strategic_analysis,
            "current_phase": "delegation",
            "messages": safe_get_state_attr(state, "messages", []) + [f"CTO strategic analysis with {team_structure.complexity_score:.1f}/10 complexity: {strategic_analysis[:200]}..."]
        }
        
    except Exception as e:
        print(f"Error in LLM CTO: {e}")
        # Fallback to basic structure
        fallback_team = states.ComplexityBasedTeamStructure()
        return {
            "work_queue": [
                states.WorkItem(id="work_1", title="Basic Development", description="Basic development work", priority=2, created_by="cto_fallback")
            ],
            "active_managers": ["manager_0"],
            "team_structure": fallback_team,
            "iteration_state": states.IterationState(),
            "current_phase": "delegation"
        }


async def llm_iteration_manager(state: states.State, config: RunnableConfig) -> Dict[str, Any]:
    """Manages iteration transitions and state updates for multi-iteration workflows."""
    print("🔄 LLM Iteration Manager: Managing Iteration Transitions")
    print("=" * 60)
    
    iteration_state = safe_get_state_attr(state, "iteration_state", states.IterationState())
    
    if not iteration_state.is_iterative:
        print("   ❌ Not in iterative mode, skipping iteration management")
        return {"current_phase": "review"}
    
    # Record results from current iteration
    current_iteration = iteration_state.current_iteration
    completed_work = [w for w in safe_get_state_attr(state, "completed_work", []) 
                     if w.iteration_batch == current_iteration]
    
    iteration_result = {
        "iteration": current_iteration + 1,
        "completed_work": completed_work,
        "summary": f"Iteration {current_iteration + 1} completed {len(completed_work)} work items"
    }
    
    # Update iteration state
    updated_iteration_state = states.IterationState(
        is_iterative=iteration_state.is_iterative,
        current_iteration=current_iteration + 1,
        total_iterations=iteration_state.total_iterations,
        iteration_work_batches=iteration_state.iteration_work_batches,
        iteration_results=iteration_state.iteration_results + [iteration_result],
        iteration_summaries=iteration_state.iteration_summaries + [iteration_result["summary"]]
    )
    
    # Check if we have more iterations
    if updated_iteration_state.current_iteration >= updated_iteration_state.total_iterations:
        print(f"   ✅ All iterations complete ({updated_iteration_state.total_iterations})")
        return {
            "iteration_state": updated_iteration_state,
            "current_phase": "review",
            "messages": safe_get_state_attr(state, "messages", []) + [f"All {updated_iteration_state.total_iterations} iterations completed"]
        }
    
    print(f"   ➡️  Advancing to iteration {updated_iteration_state.current_iteration + 1}/{updated_iteration_state.total_iterations}")
    
    # Reset manager state for next iteration
    team_structure = safe_get_state_attr(state, "team_structure", states.ComplexityBasedTeamStructure())
    manager_ids = [f"manager_{i}" for i in range(team_structure.recommended_managers)]
    
    # Reset work items status for next iteration
    next_batch_ids = (updated_iteration_state.iteration_work_batches[updated_iteration_state.current_iteration]
                     if updated_iteration_state.current_iteration < len(updated_iteration_state.iteration_work_batches)
                     else [])
    
    updated_work_queue = safe_get_state_attr(state, "work_queue", []).copy()
    for work_item in updated_work_queue:
        if work_item.id in next_batch_ids:
            work_item.status = "pending"
            work_item.assigned_to = None
    
    return {
        "iteration_state": updated_iteration_state,
        "active_managers": manager_ids,
        "active_engineers": {},  # Reset engineer assignments
        "work_queue": updated_work_queue,
        "current_phase": "delegation",
        "messages": safe_get_state_attr(state, "messages", []) + [f"Iteration {updated_iteration_state.current_iteration + 1} started with {len(next_batch_ids)} work items"]
    }


async def llm_engineering_manager(state: states.State, config: RunnableConfig) -> Dict[str, Any]:
    """LLM-powered Engineering Manager for team coordination with dynamic team sizing."""
    print("👨‍💼 LLM Engineering Manager: Dynamic Team Coordination")
    print("=" * 60)
    
    model = get_model_for_agent("engineering_manager")
    tools = get_all_tools()
    model_with_tools = model.bind_tools(tools)
    
    # Get team structure from state
    team_structure = safe_get_state_attr(state, "team_structure", states.ComplexityBasedTeamStructure())
    iteration_state = safe_get_state_attr(state, "iteration_state", states.IterationState())
    
    print(f"   📊 Using Dynamic Team Structure:")
    print(f"      Managers: {team_structure.recommended_managers}")
    print(f"      Engineers per Manager: {team_structure.recommended_engineers_per_manager}")
    print(f"      Complexity Score: {team_structure.complexity_score:.1f}/10.0")
    
    if not safe_get_state_attr(state, "active_managers", []):
        return {"current_phase": "execution"}
    
    current_manager = safe_get_state_attr(state, "active_managers", [])[0]
    
    # Filter work for current iteration if using iterations
    available_work = []
    if iteration_state.is_iterative:
        current_batch_ids = iteration_state.iteration_work_batches[iteration_state.current_iteration] if iteration_state.current_iteration < len(iteration_state.iteration_work_batches) else []
        available_work = [w for w in safe_get_state_attr(state, "work_queue", []) if w.status == "pending" and w.id in current_batch_ids]
        print(f"   🔄 Iteration {iteration_state.current_iteration + 1}/{iteration_state.total_iterations}")
        print(f"      Work items in current batch: {len(available_work)}")
    else:
        available_work = [w for w in safe_get_state_attr(state, "work_queue", []) if w.status == "pending"]
    
    if not available_work:
        print("   ⚠️  No available work for current manager")
        return {"current_phase": "execution"}
    
    system_prompt = f"""You are an Engineering Manager responsible for team building and work delegation.

    TEAM STRUCTURE (Based on Complexity Analysis):
    - Complexity Score: {team_structure.complexity_score:.1f}/10.0
    - Engineers per Manager: {team_structure.recommended_engineers_per_manager}
    - Analysis Reasoning: {team_structure.analysis_reasoning}
    
    Your responsibilities:
    - Build balanced engineering teams based on complexity analysis
    - Delegate work based on engineer specializations and team capacity
    - Coordinate between team members
    - Ensure work is properly distributed
    - Use the recommended team size for optimal performance

    You can create teams with:
    - 1 QA Engineer (for testing and quality assurance)
    - {team_structure.recommended_engineers_per_manager} Senior Engineers (for development work)

    Available work items: {[w.title for w in available_work]}
    Current manager: {current_manager}
    
    {'ITERATION MODE: Working on batch ' + str(iteration_state.current_iteration + 1) + ' of ' + str(iteration_state.total_iterations) if iteration_state.is_iterative else 'SINGLE ITERATION MODE'}

    Analyze the work and create appropriate team assignments based on the complexity-driven team structure."""
    
    work_descriptions = "\n".join([f"- {w.title}: {w.description}" for w in available_work[:5]])
    
    human_message = f"""Please analyze this work and create team assignments:

    {work_descriptions}

    Create a team structure with {team_structure.recommended_engineers_per_manager} engineers and assign work appropriately.
    Consider the complexity score of {team_structure.complexity_score:.1f}/10.0 when making assignments."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message)
    ]
    
    try:
        response = await model_with_tools.ainvoke(messages)
        delegation_plan = response.content
        
        # Create team structure based on complexity analysis
        qa_engineer = f"{current_manager}_qa_engineer"
        senior_engineer_ids = [f"{current_manager}_senior_eng_{i}" for i in range(team_structure.recommended_engineers_per_manager)]
        team_members = [qa_engineer] + senior_engineer_ids
        
        print(f"   👥 Creating Team for {current_manager}:")
        print(f"      QA Engineer: {qa_engineer}")
        print(f"      Senior Engineers: {', '.join(senior_engineer_ids)}")
        
        # Assign work based on LLM recommendations and team capacity
        max_work_items = min(len(available_work), len(team_members))
        manager_work = available_work[:max_work_items]
        
        for i, work_item in enumerate(manager_work):
            if i == 0:
                # First item to QA Engineer
                work_item.assigned_to = qa_engineer
                work_item.status = "assigned"
                print(f"   📋 Assigned '{work_item.title}' to QA Engineer: {qa_engineer}")
            else:
                # Distribute remaining work to Senior Engineers
                engineer_index = (i - 1) % len(senior_engineer_ids)
                assigned_engineer = senior_engineer_ids[engineer_index]
                work_item.assigned_to = assigned_engineer
                work_item.status = "assigned"
                print(f"   📋 Assigned '{work_item.title}' to Senior Engineer: {assigned_engineer}")
        
        # Update state
        updated_work_queue = [w for w in safe_get_state_attr(state, "work_queue", []) if w not in manager_work] + manager_work
        updated_active_engineers = safe_get_state_attr(state, "active_engineers", {}).copy()
        updated_active_engineers[current_manager] = team_members
        remaining_managers = safe_get_state_attr(state, "active_managers", [])[1:]
        
        # Check for iteration advancement
        next_phase = "execution" if not remaining_managers else "delegation"
        
        # Handle iteration completion
        if iteration_state.is_iterative and not remaining_managers:
            if iteration_state.current_iteration + 1 < iteration_state.total_iterations:
                print(f"   🔄 Iteration {iteration_state.current_iteration + 1} complete, {iteration_state.total_iterations - iteration_state.current_iteration - 1} remaining")
                # Will need iteration management in routing
        
        return {
            "work_queue": updated_work_queue,
            "active_managers": remaining_managers,
            "active_engineers": updated_active_engineers,
            "delegation_plan": delegation_plan,
            "current_phase": next_phase,
            "messages": safe_get_state_attr(state, "messages", []) + [f"Engineering Manager ({team_structure.recommended_engineers_per_manager} engineers): {delegation_plan[:200]}..."]
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
    senior_work = [w for w in safe_get_state_attr(state, "work_queue", []) if w.status == "assigned" and w.assigned_to and "senior_eng" in w.assigned_to]
    
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
    - IMPORTANT: If you encounter access limitations, missing credentials, or capability gaps, clearly identify them in your response

    Current assignment: {work_item.title}
    Description: {work_item.description}
    Engineer ID: {engineer_id}

    If you encounter any of these issues, clearly state them:
    - Missing credentials or API keys
    - Insufficient access permissions
    - Missing tools or software
    - Platform/service unavailability
    - Need for approvals or escalations

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
        
        # Check for capability gaps in the response
        import human_assistance
        
        capability_keywords = [
            "access denied", "unauthorized", "missing credentials", "insufficient permissions",
            "tool not available", "platform unavailable", "need approval", "escalation required",
            "cannot access", "missing api key", "authentication failed", "permission denied"
        ]
        
        has_capability_gap = any(keyword in implementation_details.lower() for keyword in capability_keywords)
        
        if has_capability_gap:
            print(f"   ⚠️  Capability gap detected in {engineer_id}'s work")
            
            # Identify specific gaps
            gaps = human_assistance.identify_capability_gaps(implementation_details, work_item.description)
            
            if gaps:
                # Create assistance request for the primary gap
                primary_gap = gaps[0]  # Take the first identified gap
                
                assistance_request = human_assistance.create_assistance_request(
                    work_item_id=work_item.id,
                    engineer_id=engineer_id,
                    request_type=primary_gap.gap_type.replace("missing_", "").replace("insufficient_", "").replace("_", " "),
                    title=f"Access/Capability Issue: {work_item.title}",
                    description=f"Engineer {engineer_id} encountered capability gap: {primary_gap.description}",
                    urgency=primary_gap.impact_level,
                    required_capabilities=[primary_gap.resource_name],
                    blocked_tasks=[work_item.title],
                    suggested_solution=primary_gap.alternative_description if primary_gap.alternative_available else None
                )
                
                # Mark work as blocked pending human assistance
                work_item.status = "blocked"
                work_item.result = f"BLOCKED - Capability gap detected by {engineer_id}: {implementation_details}"
                
                updated_work_queue = safe_get_state_attr(state, "work_queue", []).copy()
                for i, w in enumerate(updated_work_queue):
                    if w.id == work_item.id:
                        updated_work_queue[i] = work_item
                        break
                
                updated_requests = safe_get_state_attr(state, "human_assistance_requests", []) + [assistance_request]
                
                return {
                    "work_queue": updated_work_queue,
                    "human_assistance_requests": updated_requests,
                    "pending_human_intervention": True,
                    "current_phase": "human_assistance",
                    "implementation_details": f"Capability gap detected: {implementation_details}",
                    "messages": safe_get_state_attr(state, "messages", []) + [f"Senior Engineer {engineer_id}: Capability gap detected, human assistance requested"]
                }
        
        print(f"   LLM Senior Engineer {engineer_id} completed: {work_item.title}")
        
        # Mark work as entering evaluation
        work_item.status = "evaluation"
        work_item.result = f"Development completed by {engineer_id}: {implementation_details}"
        work_item.evaluation_loop = states.EvaluationLoop()
        
        updated_work_queue = safe_get_state_attr(state, "work_queue", []).copy()
        for i, w in enumerate(updated_work_queue):
            if w.id == work_item.id:
                updated_work_queue[i] = work_item
                break
        
        evaluation_queue = safe_get_state_attr(state, "evaluation_queue", []) + [work_item]
        remaining_assigned = [w for w in updated_work_queue if w.status == "assigned"]
        next_phase = "evaluation" if evaluation_queue else ("review" if not remaining_assigned else "execution")
        
        return {
            "work_queue": updated_work_queue,
            "evaluation_queue": evaluation_queue,
            "implementation_details": implementation_details,
            "current_phase": next_phase,
            "messages": safe_get_state_attr(state, "messages", []) + [f"Senior Engineer {engineer_id}: {implementation_details[:200]}..."]
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
    qa_work = [w for w in safe_get_state_attr(state, "work_queue", []) if w.status == "assigned" and w.assigned_to and "qa_engineer" in w.assigned_to]
    
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
        
        updated_work_queue = safe_get_state_attr(state, "work_queue", []).copy()
        for i, w in enumerate(updated_work_queue):
            if w.id == work_item.id:
                updated_work_queue[i] = work_item
                break
        
        completed_work = safe_get_state_attr(state, "completed_work", []) + [work_item]
        remaining_assigned = [w for w in updated_work_queue if w.status == "assigned"]
        next_phase = "review" if not remaining_assigned else "execution"
        
        return {
            "work_queue": updated_work_queue,
            "completed_work": completed_work,
            "qa_results": qa_results,
            "current_phase": next_phase,
            "messages": safe_get_state_attr(state, "messages", []) + [f"QA Engineer {engineer_id}: {qa_results[:200]}..."]
        }
        
    except Exception as e:
        print(f"Error in LLM QA Engineer: {e}")
        return {"current_phase": "execution"}


async def llm_senior_engineer_aggregator(state: states.State, config: RunnableConfig) -> Dict[str, Any]:
    """Aggregates outputs from multiple senior engineers working in parallel on different tasks."""
    
    # Get completed development work from senior engineers that passed evaluation
    completed_senior_work = [w for w in safe_get_state_attr(state, "evaluation_queue", []) if 
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
    updated_work_queue = [w for w in safe_get_state_attr(state, "work_queue", []) if w not in completed_senior_work] + [aggregated_work]
    
    # Remove completed items from evaluation queue
    updated_evaluation_queue = [w for w in safe_get_state_attr(state, "evaluation_queue", []) if w not in completed_senior_work]
    
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
    
    completed_count = len(safe_get_state_attr(state, "completed_work", []))
    total_managers = len(safe_get_state_attr(state, "active_engineers", {}))
    
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
    
    Recent messages: {safe_get_state_attr(state, 'messages', [])[-5:] if safe_get_state_attr(state, 'messages') else 'No recent messages'}
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
            "messages": safe_get_state_attr(state, "messages", []) + [f"Final review: {review_analysis[:200]}..."]
        }
        
    except Exception as e:
        print(f"Error in LLM Review: {e}")
        # Fallback to basic review
        return {
            "review_analysis": f"Project completed: {completed_count} items, {total_managers} teams",
            "current_phase": "completed"
        }


async def llm_human_assistance_coordinator(state: states.State, config: RunnableConfig) -> Dict[str, Any]:
    """Coordinates human assistance requests and capability gap resolution."""
    print("🤝 Human Assistance Coordinator: Processing Requests")
    print("=" * 55)
    
    import human_assistance
    
    # Get pending assistance requests
    pending_requests = human_assistance.get_pending_assistance_requests(state)
    
    if not pending_requests:
        print("   No pending human assistance requests")
        return {"current_phase": "execution", "pending_human_intervention": False}
    
    print(f"   Processing {len(pending_requests)} assistance request(s)")
    
    # Group requests by urgency
    critical_requests = [r for r in pending_requests if r.urgency == "critical"]
    high_requests = [r for r in pending_requests if r.urgency == "high"]
    medium_requests = [r for r in pending_requests if r.urgency == "medium"]
    low_requests = [r for r in pending_requests if r.urgency == "low"]
    
    # Format summary for human review
    summary_parts = []
    
    if critical_requests:
        summary_parts.append("🔴 CRITICAL REQUESTS:")
        for req in critical_requests:
            summary_parts.append(human_assistance.format_assistance_request_summary(req))
    
    if high_requests:
        summary_parts.append("🟠 HIGH PRIORITY REQUESTS:")
        for req in high_requests:
            summary_parts.append(human_assistance.format_assistance_request_summary(req))
    
    if medium_requests:
        summary_parts.append("🟡 MEDIUM PRIORITY REQUESTS:")
        for req in medium_requests:
            summary_parts.append(human_assistance.format_assistance_request_summary(req))
    
    if low_requests:
        summary_parts.append("🟢 LOW PRIORITY REQUESTS:")
        for req in low_requests:
            summary_parts.append(human_assistance.format_assistance_request_summary(req))
    
    assistance_summary = "\n".join(summary_parts)
    
    # Mark as needing human intervention
    print(f"   Assistance requests require human intervention")
    print(f"   Summary prepared for human review")
    
    return {
        "current_phase": "human_assistance",
        "pending_human_intervention": True,
        "messages": safe_get_state_attr(state, "messages", []) + [f"Human Assistance Coordinator: {len(pending_requests)} requests pending human review"],
        "implementation_details": safe_get_state_attr(state, "implementation_details", "") + f"\n\nHUMAN ASSISTANCE REQUIRED:\n{assistance_summary}"
    }


async def llm_capability_gap_analyzer(state: states.State, config: RunnableConfig) -> Dict[str, Any]:
    """Analyzes capability gaps and creates assistance requests when needed."""
    print("🔍 Capability Gap Analyzer: Analyzing Limitations")
    print("=" * 50)
    
    import human_assistance
    
    # Look for work items that might have capability gaps
    problem_work = []
    
    # Check failed work items
    for work_item in safe_get_state_attr(state, "failed_work", []):
        if work_item.result and any(keyword in work_item.result.lower() for keyword in 
                                   ["error", "failed", "unauthorized", "access denied", "missing"]):
            problem_work.append(work_item)
    
    # Check work items stuck in evaluation loops
    for work_item in safe_get_state_attr(state, "evaluation_queue", []):
        if work_item.evaluation_loop.loop_count >= 2:  # Multiple failed attempts
            problem_work.append(work_item)
    
    if not problem_work:
        print("   No capability gaps detected")
        return {"current_phase": safe_get_state_attr(state, "current_phase", "execution")}
    
    print(f"   Analyzing {len(problem_work)} problematic work item(s)")
    
    new_requests = []
    
    for work_item in problem_work:
        # Analyze the specific failure
        error_context = work_item.result or "Multiple evaluation failures"
        
        # Identify capability gaps
        gaps = human_assistance.identify_capability_gaps(error_context, work_item.description)
        
        if gaps:
            print(f"   Found capability gaps in: {work_item.title}")
            
            # Create assistance request for the most critical gap
            primary_gap = max(gaps, key=lambda g: ["low", "medium", "high", "critical"].index(g.impact_level))
            
            request = human_assistance.create_assistance_request(
                work_item_id=work_item.id,
                engineer_id=work_item.assigned_to or "unassigned",
                request_type=primary_gap.gap_type.replace("_", " "),
                title=f"Capability Gap: {primary_gap.resource_name}",
                description=f"Work item '{work_item.title}' blocked by {primary_gap.description}",
                urgency=primary_gap.impact_level,
                required_capabilities=[primary_gap.resource_name],
                blocked_tasks=[work_item.title],
                suggested_solution=primary_gap.alternative_description if primary_gap.alternative_available else None
            )
            
            new_requests.append(request)
    
    if new_requests:
        updated_requests = safe_get_state_attr(state, "human_assistance_requests", []) + new_requests
        print(f"   Created {len(new_requests)} assistance request(s)")
        
        return {
            "human_assistance_requests": updated_requests,
            "pending_human_intervention": True,
            "current_phase": "human_assistance",
            "messages": safe_get_state_attr(state, "messages", []) + [f"Capability Gap Analyzer: Created {len(new_requests)} assistance requests"]
        }
    
    return {"current_phase": safe_get_state_attr(state, "current_phase", "execution")}
