"""Evaluator functions for the quality assurance pipeline.

Complete evaluator-optimizer pattern implementation with:
- Sequential evaluation stages
- Loop-based optimization cycles  
- Escalation mechanisms
- Human-in-the-loop intervention
"""

from typing import Any, Dict
import states


def unit_test_evaluator(state: states.State) -> Dict[str, Any]:
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


def self_review_evaluator(state: states.State) -> Dict[str, Any]:
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


def peer_review_evaluator(state: states.State) -> Dict[str, Any]:
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


def integration_test_evaluator(state: states.State) -> Dict[str, Any]:
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


def manager_review_evaluator(state: states.State) -> Dict[str, Any]:
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


def cto_review_evaluator(state: states.State) -> Dict[str, Any]:
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


def human_escalation_evaluator(state: states.State) -> Dict[str, Any]:
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
