"""Routing functions for workflow transitions with iteration support.

Conditional logic for determining next steps in:
- Manager delegation workflows with dynamic team sizing
- Engineer assignment patterns with complexity-based teams
- Evaluation pipeline progression
- Multi-iteration execution for large projects
"""

from typing import Literal
import states


def safe_get_state_attr(state: states.State, key: str, default=None):
    """Safely get state attribute whether state is dict-like or object-like."""
    if hasattr(state, 'get'):
        return safe_get_state_attr(state, key, default)
    return getattr(state, key, default)


def should_continue_with_managers(state: states.State) -> Literal["engineering_manager", "execution", "cto", "review"]:
    """Route to manager delegation, next iteration, or review phase."""
    iteration_state = safe_get_state_attr(state, "iteration_state", states.IterationState())
    
    # Standard delegation flow
    if state.current_phase == "delegation" and state.active_managers:
        return "engineering_manager"
    
    # Check for iteration advancement
    if iteration_state.is_iterative:
        # If we've completed current iteration and have more to go
        if (not state.active_managers and 
            iteration_state.current_iteration + 1 < iteration_state.total_iterations):
            
            print(f"🔄 Advancing to iteration {iteration_state.current_iteration + 2}/{iteration_state.total_iterations}")
            return "cto"  # Go back to CTO to set up next iteration
    
    # Check if there's more execution work to do
    assigned_work = [w for w in state.work_queue if w.status == "assigned"]
    if assigned_work:
        return "execution"
    
    return "review"


def should_continue_with_engineers(state: states.State) -> Literal["senior_engineer", "senior_engineer_aggregator", "qa_engineer", "evaluation", "capability_gap_analyzer", "human_assistance_coordinator", "cto", "review"]:
    """Route to appropriate engineer type, aggregator, evaluation phase, capability analysis, human assistance, next iteration, or review phase."""
    iteration_state = safe_get_state_attr(state, "iteration_state", states.IterationState())
    
    # Check for pending human assistance requests
    if safe_get_state_attr(state, "pending_human_intervention", False):
        pending_requests = [req for req in safe_get_state_attr(state, "human_assistance_requests", []) if req.status == "pending"]
        if pending_requests:
            return "human_assistance_coordinator"
    
    # Check for blocked work that might need capability gap analysis
    blocked_work = [w for w in state.work_queue if w.status == "blocked"]
    if blocked_work:
        return "capability_gap_analyzer"
    
    assigned_work = [w for w in state.work_queue if w.status == "assigned"]
    evaluation_work = [w for w in state.evaluation_queue if w.status == "evaluation"]
    
    # Check if there's work in evaluation queue
    if evaluation_work:
        return "evaluation"
    
    # Check for iteration advancement before checking for review
    if iteration_state.is_iterative and not assigned_work:
        # If no assigned work and we can advance iteration
        if iteration_state.current_iteration + 1 < iteration_state.total_iterations:
            print(f"🔄 Execution complete for iteration {iteration_state.current_iteration + 1}, advancing to next iteration")
            return "cto"  # Return to CTO to setup next iteration
    
    if not assigned_work:
        return "review"
    
    # Filter work by current iteration if in iterative mode
    if iteration_state.is_iterative:
        current_batch_ids = (iteration_state.iteration_work_batches[iteration_state.current_iteration] 
                           if iteration_state.current_iteration < len(iteration_state.iteration_work_batches) 
                           else [])
        assigned_work = [w for w in assigned_work if w.id in current_batch_ids]
        
        if not assigned_work:
            # No work in current iteration batch, check if we can advance
            if iteration_state.current_iteration + 1 < iteration_state.total_iterations:
                return "cto"
            else:
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


def should_continue_with_evaluation(state: states.State) -> Literal["unit_test_evaluator", "self_review_evaluator", "peer_review_evaluator", "integration_test_evaluator", "manager_review_evaluator", "cto_review_evaluator", "human_escalation_evaluator", "capability_gap_analyzer", "execution", "review"]:
    """Route to appropriate evaluation stage, capability analysis, or back to execution."""
    
    # Check if there are any items in evaluation queue
    if not state.evaluation_queue:
        # Check for failed work that might need capability gap analysis
        failed_work = [w for w in safe_get_state_attr(state, "failed_work", []) if 
                      w.result and any(keyword in w.result.lower() for keyword in 
                                     ["error", "failed", "unauthorized", "access denied"])]
        if failed_work:
            return "capability_gap_analyzer"
        
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


def should_route_from_human_assistance(state: states.State) -> Literal["execution", "capability_gap_analyzer", "review"]:
    """Route from human assistance phase back to appropriate workflow stage."""
    
    # Check if there are still pending requests
    pending_requests = [req for req in safe_get_state_attr(state, "human_assistance_requests", []) if req.status == "pending"]
    if pending_requests:
        return "capability_gap_analyzer"  # Continue analyzing capability gaps
    
    # Check if there's work to be done
    assigned_work = [w for w in state.work_queue if w.status == "assigned"]
    blocked_work = [w for w in state.work_queue if w.status == "blocked"]
    
    # If we have blocked work, it might be unblocked now
    if blocked_work:
        return "capability_gap_analyzer"
    
    # Resume normal execution
    return "execution" if assigned_work else "review"
