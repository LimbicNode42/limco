from typing import List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage


class RecoveryState(TypedDict):
    """
    Represents the state of the data recovery process.
    """

    available_drives: Optional[List[str]]
    selected_drive: Optional[str]
    clone_path: Optional[str]
    analysis_results: Optional[dict]
    recovery_plan: Optional[str]
    human_approval: Optional[bool]
    error: Optional[str]
    messages: List[BaseMessage]
    # Add explicit fields for user input
    awaiting_drive_selection: Optional[bool]
    awaiting_approval: Optional[bool]
