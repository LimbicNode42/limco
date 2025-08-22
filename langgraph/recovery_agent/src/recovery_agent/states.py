from typing import List, Optional, Dict, Any
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage


class RecoveryState(TypedDict):
    """
    Represents the state of the data recovery process.
    """

    # Drive detection and selection
    available_drives: Optional[List[str]]
    drive_details: Optional[List[Dict[str, str]]]  # Detailed drive information
    selected_drive: Optional[str]
    
    # Cloning and analysis
    clone_path: Optional[str]
    analysis_results: Optional[Dict[str, str]]  # partition -> status mapping
    
    # Recovery planning and execution
    recovery_plan: Optional[str]
    recovery_completed: Optional[bool]
    
    # Human interaction
    human_approval: Optional[bool]
    awaiting_drive_selection: Optional[bool]
    awaiting_approval: Optional[bool]
    
    # System state
    error: Optional[str]
    messages: List[BaseMessage]
    awaiting_drive_selection: Optional[bool]
    awaiting_approval: Optional[bool]
