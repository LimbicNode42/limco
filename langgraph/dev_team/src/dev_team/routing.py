"""Routing functions for workflow transitions.

Conditional logic for determining next steps in:
- Manager delegation workflows
- Engineer assignment patterns  
- Evaluation pipeline progression
"""

from typing import Literal
import states


def should_continue_with_managers(state: states.State) -> Literal["engineering_manager", "review"]:
    """Route to manager delegation or review phase."""
    if state.current_phase == "delegation" and state.active_managers:
        return "engineering_manager"
    return "review"


def should_continue_with_engineers(state: states.State) -> Literal["senior_engineer", "senior_engineer_aggregator", "qa_engineer", "evaluation", "review"]:
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


def should_continue_with_evaluation(state: states.State) -> Literal["unit_test_evaluator", "self_review_evaluator", "peer_review_evaluator", "integration_test_evaluator", "manager_review_evaluator", "cto_review_evaluator", "human_escalation_evaluator", "execution", "review"]:
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
