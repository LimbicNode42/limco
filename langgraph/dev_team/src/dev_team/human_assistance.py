"""
Human-in-the-loop assistance system for handling capability gaps and access limitations.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import states


def create_assistance_request(
    work_item_id: str,
    engineer_id: str,
    request_type: str,
    title: str,
    description: str,
    urgency: str = "medium",
    required_capabilities: List[str] = None,
    blocked_tasks: List[str] = None,
    suggested_solution: Optional[str] = None
) -> states.HumanAssistanceRequest:
    """Create a new human assistance request."""
    
    return states.HumanAssistanceRequest(
        id=str(uuid.uuid4()),
        work_item_id=work_item_id,
        engineer_id=engineer_id,
        request_type=request_type,
        title=title,
        description=description,
        urgency=urgency,
        required_capabilities=required_capabilities or [],
        blocked_tasks=blocked_tasks or [],
        suggested_solution=suggested_solution,
        status="pending",
        created_at=datetime.now()
    )


def identify_capability_gaps(error_message: str, task_description: str) -> List[states.CapabilityGap]:
    """Analyze error messages and task descriptions to identify capability gaps."""
    
    gaps = []
    error_lower = error_message.lower()
    task_lower = task_description.lower()
    
    # Common patterns that indicate specific capability gaps
    gap_patterns = {
        "missing_credentials": [
            "authentication failed", "unauthorized", "invalid credentials", 
            "access denied", "login required", "api key", "token expired"
        ],
        "insufficient_access": [
            "permission denied", "forbidden", "insufficient privileges", 
            "admin access required", "not authorized"
        ],
        "missing_tools": [
            "command not found", "module not found", "tool not available",
            "package not installed", "dependency missing"
        ],
        "platform_unavailable": [
            "service unavailable", "connection refused", "endpoint not found",
            "server not responding", "network unreachable"
        ],
        "permission_required": [
            "approval required", "requires supervisor", "needs sign-off",
            "escalation needed", "compliance check"
        ]
    }
    
    # Check for patterns in error messages
    for gap_type, patterns in gap_patterns.items():
        for pattern in patterns:
            if pattern in error_lower or pattern in task_lower:
                gaps.append(states.CapabilityGap(
                    gap_type=gap_type,
                    resource_name=_extract_resource_name(error_message, pattern),
                    description=f"Detected {gap_type.replace('_', ' ')}: {pattern}",
                    impact_level=_assess_impact_level(gap_type, task_description),
                    alternative_available=_check_alternatives(gap_type, task_description)
                ))
                break  # Only add one gap per type to avoid duplicates
    
    return gaps


def _extract_resource_name(error_message: str, pattern: str) -> str:
    """Extract the resource name from error message context."""
    # Simple extraction - could be enhanced with regex
    words = error_message.split()
    try:
        pattern_index = next(i for i, word in enumerate(words) if pattern.lower() in word.lower())
        # Look for resource name near the pattern
        if pattern_index > 0:
            return words[pattern_index - 1]
        elif pattern_index < len(words) - 1:
            return words[pattern_index + 1]
    except (StopIteration, IndexError):
        pass
    
    return "unknown_resource"


def _assess_impact_level(gap_type: str, task_description: str) -> str:
    """Assess the impact level of a capability gap."""
    task_lower = task_description.lower()
    
    # High impact indicators
    if any(keyword in task_lower for keyword in ["critical", "production", "security", "deployment"]):
        return "high"
    
    # Medium impact by default for most gaps
    if gap_type in ["missing_credentials", "insufficient_access", "platform_unavailable"]:
        return "medium"
    
    # Low impact for tool-related issues (often have alternatives)
    return "low"


def _check_alternatives(gap_type: str, task_description: str) -> bool:
    """Check if alternatives might be available for this capability gap."""
    # Tool-related gaps often have alternatives
    if gap_type == "missing_tools":
        return True
    
    # Platform issues might have alternative approaches
    if gap_type == "platform_unavailable":
        return True
    
    # Access and credential issues typically don't have alternatives
    return False


def format_assistance_request_summary(request: states.HumanAssistanceRequest) -> str:
    """Format a human assistance request for display."""
    
    urgency_emoji = {
        "low": "🟢",
        "medium": "🟡", 
        "high": "🟠",
        "critical": "🔴"
    }
    
    type_emoji = {
        "credentials": "🔑",
        "access": "🚪",
        "tools": "🔧",
        "platform": "🖥️",
        "approval": "✅",
        "clarification": "❓"
    }
    
    emoji = urgency_emoji.get(request.urgency, "⚪")
    type_icon = type_emoji.get(request.request_type, "📋")
    
    summary = f"{emoji} {type_icon} **{request.title}**\n"
    summary += f"   Engineer: {request.engineer_id}\n"
    summary += f"   Type: {request.request_type.title()}\n"
    summary += f"   Urgency: {request.urgency.title()}\n"
    summary += f"   Description: {request.description}\n"
    
    if request.required_capabilities:
        summary += f"   Required: {', '.join(request.required_capabilities)}\n"
    
    if request.blocked_tasks:
        summary += f"   Blocking: {', '.join(request.blocked_tasks)}\n"
    
    if request.suggested_solution:
        summary += f"   Suggestion: {request.suggested_solution}\n"
    
    return summary


def resolve_assistance_request(
    request: states.HumanAssistanceRequest,
    human_response: str,
    provided_credentials: Dict[str, str] = None,
    provided_access: List[str] = None,
    notes: List[str] = None
) -> states.HumanAssistanceRequest:
    """Mark an assistance request as resolved with human response."""
    
    request.status = "resolved"
    request.resolved_at = datetime.now()
    request.human_response = human_response
    request.provided_credentials.update(provided_credentials or {})
    request.provided_access.extend(provided_access or [])
    request.notes.extend(notes or [])
    
    return request


def get_pending_assistance_requests(state: states.State) -> List[states.HumanAssistanceRequest]:
    """Get all pending human assistance requests."""
    return [req for req in state.human_assistance_requests if req.status == "pending"]


def get_assistance_requests_for_engineer(state: states.State, engineer_id: str) -> List[states.HumanAssistanceRequest]:
    """Get all assistance requests for a specific engineer."""
    return [req for req in state.human_assistance_requests if req.engineer_id == engineer_id]


def check_if_human_intervention_needed(state: states.State) -> bool:
    """Check if there are any pending human assistance requests."""
    return len(get_pending_assistance_requests(state)) > 0


def create_capability_gap_summary(gaps: List[states.CapabilityGap]) -> str:
    """Create a summary of identified capability gaps."""
    if not gaps:
        return "No capability gaps identified."
    
    summary = f"Identified {len(gaps)} capability gap(s):\n"
    
    for i, gap in enumerate(gaps, 1):
        impact_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}
        emoji = impact_emoji.get(gap.impact_level, "⚪")
        
        summary += f"{i}. {emoji} {gap.gap_type.replace('_', ' ').title()}: {gap.resource_name}\n"
        summary += f"   Description: {gap.description}\n"
        summary += f"   Impact: {gap.impact_level.title()}\n"
        
        if gap.alternative_available and gap.alternative_description:
            summary += f"   Alternative: {gap.alternative_description}\n"
        elif gap.alternative_available:
            summary += f"   Alternative: May be available\n"
        
        summary += "\n"
    
    return summary
