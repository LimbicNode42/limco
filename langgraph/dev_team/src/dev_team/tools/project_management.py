"""Project management tools."""

from datetime import datetime
from langchain_core.tools import tool


@tool
def create_task(title: str, description: str, assignee: str = None, priority: str = "medium") -> str:
    """Create a new project task.
    
    Args:
        title: Task title
        description: Detailed task description
        assignee: Person assigned to the task
        priority: Task priority (low, medium, high, critical)
        
    Returns:
        Task creation confirmation with ID
    """
    task_id = f"TASK-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    return f"Task created: {title} (ID: {task_id}, Assignee: {assignee}, Priority: {priority})"


@tool
def update_task_status(task_id: str, status: str, notes: str = "") -> str:
    """Update the status of an existing task.
    
    Args:
        task_id: The task identifier
        status: New status (todo, in_progress, review, done, blocked)
        notes: Optional notes about the status change
        
    Returns:
        Status update confirmation
    """
    return f"Task {task_id} status updated to '{status}'. Notes: {notes}"


@tool
def get_team_workload() -> str:
    """Get current workload distribution across team members.
    
    Returns:
        Team workload summary
    """
    return """Team Workload:
- Alice (Senior Engineer): 8 tasks (3 in progress)
- Bob (QA Engineer): 5 tasks (2 in progress)
- Carol (Engineering Manager): 12 tasks (5 in progress)
- Dave (Senior Engineer): 6 tasks (2 in progress)"""


__all__ = [
    'create_task',
    'update_task_status',
    'get_team_workload'
]
