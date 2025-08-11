"""Agent handoff and collaboration tools."""

from typing import Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.types import Command  
from langgraph.prebuilt import InjectedState


def safe_get_state_attr(state: dict, key: str, default=None):
    """Safely get state attribute whether state is dict-like or object-like."""
    if hasattr(state, 'get'):
        return state.get(key, default)
    return getattr(state, key, default)


@tool
def transfer_to_qa_engineer(
    reason: Annotated[str, "Reason for transferring to QA"],
    context: Annotated[str, "Context and details for QA engineer"],
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    priority: str = "medium"
) -> Command:
    """Transfer work to QA engineer for testing and quality assurance."""
    tool_message = {
        "role": "tool",
        "content": f"Work transferred to QA engineer. Reason: {reason}",
        "name": "transfer_to_qa_engineer",
        "tool_call_id": tool_call_id,
    }
    
    return Command(
        goto="qa_engineer",
        update={
            "messages": safe_get_state_attr(state, "messages", []) + [tool_message],
            "handoff_reason": reason,
            "handoff_context": context,
            "priority": priority,
            "current_agent": "qa_engineer"
        },
        graph=Command.PARENT,
    )


@tool
def escalate_to_cto(
    issue: Annotated[str, "Issue requiring CTO attention"],
    urgency: Annotated[str, "Urgency level: low, medium, high, critical"],
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """Escalate complex technical or strategic decisions to CTO."""
    tool_message = {
        "role": "tool",
        "content": f"Issue escalated to CTO. Urgency: {urgency}",
        "name": "escalate_to_cto",
        "tool_call_id": tool_call_id,
    }
    
    return Command(
        goto="cto",
        update={
            "messages": safe_get_state_attr(state, "messages", []) + [tool_message],
            "escalation_issue": issue,
            "urgency": urgency,
            "current_agent": "cto"
        },
        graph=Command.PARENT,
    )


@tool
def request_peer_review(
    code_section: Annotated[str, "Code section requiring review"],
    review_type: Annotated[str, "Type of review needed: design, security, performance"],
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """Request peer review from senior engineering team member."""
    tool_message = {
        "role": "tool",
        "content": f"Peer review requested for {review_type} review",
        "name": "request_peer_review",
        "tool_call_id": tool_call_id,
    }
    
    return Command(
        goto="senior_engineer",
        update={
            "messages": safe_get_state_attr(state, "messages", []) + [tool_message],
            "review_code": code_section,
            "review_type": review_type,
            "current_agent": "senior_engineer"
        },
        graph=Command.PARENT,
    )


@tool
def delegate_to_engineering_manager(
    task: Annotated[str, "Task requiring engineering management"],
    reason: Annotated[str, "Reason for delegation"],
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """Delegate task to engineering manager for coordination."""
    tool_message = {
        "role": "tool",
        "content": f"Task delegated to engineering manager: {task}",
        "name": "delegate_to_engineering_manager",
        "tool_call_id": tool_call_id,
    }
    
    return Command(
        goto="engineering_manager",
        update={
            "messages": safe_get_state_attr(state, "messages", []) + [tool_message],
            "delegated_task": task,
            "delegation_reason": reason,
            "current_agent": "engineering_manager"
        },
        graph=Command.PARENT,
    )


@tool
def transfer_to_senior_engineer(
    problem: Annotated[str, "Complex problem requiring senior expertise"],
    context: Annotated[str, "Technical context and background"],
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """Transfer complex technical problem to senior engineer."""
    tool_message = {
        "role": "tool",
        "content": f"Problem transferred to senior engineer: {problem}",
        "name": "transfer_to_senior_engineer",
        "tool_call_id": tool_call_id,
    }
    
    return Command(
        goto="senior_engineer",
        update={
            "messages": safe_get_state_attr(state, "messages", []) + [tool_message],
            "technical_problem": problem,
            "problem_context": context,
            "current_agent": "senior_engineer"
        },
        graph=Command.PARENT,
    )


@tool
def escalate_to_human(
    issue: Annotated[str, "Issue requiring human intervention"],
    urgency: Annotated[str, "Urgency level: low, medium, high, critical"],
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """Escalate to human developer when AI agents cannot resolve issue."""
    tool_message = {
        "role": "tool",
        "content": f"Issue escalated to human developer. Urgency: {urgency}",
        "name": "escalate_to_human",
        "tool_call_id": tool_call_id,
    }
    
    return Command(
        goto="human_assistance",
        update={
            "messages": safe_get_state_attr(state, "messages", []) + [tool_message],
            "human_issue": issue,
            "urgency": urgency,
            "current_agent": "human_assistance"
        },
        graph=Command.PARENT,
    )


__all__ = [
    'transfer_to_qa_engineer',
    'escalate_to_cto', 
    'request_peer_review',
    'delegate_to_engineering_manager',
    'transfer_to_senior_engineer',
    'escalate_to_human'
]
