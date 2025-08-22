import subprocess
from langchain_core.messages import AIMessage, HumanMessage
from .states import RecoveryState


def detect_drives_node(state: RecoveryState) -> RecoveryState:
    """
    Detects available drives on the system.
    """
    try:
        # This is a placeholder. In a real scenario, you would use a more robust
        # method to list drives, like `lsblk` on Linux or `wmic` on Windows.
        result = subprocess.run(["echo", "drive1 /dev/sda\ndrive2 /dev/sdb"], capture_output=True, text=True, check=True)
        drives = result.stdout.strip().split("\n")
        state["available_drives"] = drives
        
        # Add message to chat
        if "messages" not in state:
            state["messages"] = []
        
        drives_list = "\n".join([f"- {drive}" for drive in drives])
        state["messages"].append(
            AIMessage(content=f"I've detected the following drives:\n{drives_list}\n\nPlease select which drive you'd like to analyze for recovery.")
        )
        
    except Exception as e:
        state["error"] = f"Failed to detect drives: {e}"
        if "messages" not in state:
            state["messages"] = []
        state["messages"].append(AIMessage(content=f"Error detecting drives: {e}"))
    
    return state


def select_drive_node(state: RecoveryState) -> RecoveryState:
    """
    Asks user to select a drive via chat. This node just asks - processing happens after interrupt.
    """
    if "messages" not in state:
        state["messages"] = []
    
    # Only ask the question if we haven't asked yet and don't have a selection
    if not state.get("selected_drive"):
        drives_list = "\n".join([f"- {drive}" for drive in state.get("available_drives", [])])
        state["messages"].append(
            AIMessage(content=f"Please select which drive you'd like to analyze:\n{drives_list}\n\nJust type the drive name (e.g., 'drive1 /dev/sda')")
        )
        # Mark that we're waiting for drive selection
        state["awaiting_drive_selection"] = True
    
    return state


def process_drive_selection_node(state: RecoveryState) -> RecoveryState:
    """
    Processes the user's drive selection from chat after interrupt.
    """
    if "messages" not in state:
        state["messages"] = []
        
    # Get the last human message for drive selection
    if state.get("messages"):
        # Look for the most recent human message
        for message in reversed(state["messages"]):
            if isinstance(message, HumanMessage):
                # Extract drive selection from the message
                user_input = message.content.strip()
                state["selected_drive"] = user_input
                
                state["messages"].append(
                    AIMessage(content=f"You selected: {user_input}. I'll now proceed to clone this drive safely.")
                )
                break
    
    return state


def clone_drive_node(state: RecoveryState) -> RecoveryState:
    """
    Clones the selected drive to a safe location.
    """
    if "messages" not in state:
        state["messages"] = []
        
    state["messages"].append(
        AIMessage(content=f"🔄 Cloning drive {state['selected_drive']}...")
    )
    
    # Placeholder for cloning logic
    state["clone_path"] = f"/path/to/clone_of_{state['selected_drive'].split('/')[-1]}.img"
    
    state["messages"].append(
        AIMessage(content=f"✅ Drive successfully cloned to {state['clone_path']}")
    )
    
    return state


def analyze_partitions_node(state: RecoveryState) -> RecoveryState:
    """
    Analyzes the partitions of the cloned drive for corruption.
    """
    if "messages" not in state:
        state["messages"] = []
        
    state["messages"].append(
        AIMessage(content=f"🔍 Analyzing partitions of {state['clone_path']}...")
    )
    
    # Placeholder for analysis logic
    state["analysis_results"] = {"partition_1": "corrupted", "partition_2": "ok"}
    
    analysis_summary = "\n".join([
        f"- {partition}: {status}" 
        for partition, status in state["analysis_results"].items()
    ])
    
    state["messages"].append(
        AIMessage(content=f"📊 Analysis complete:\n{analysis_summary}")
    )
    
    return state


def generate_recovery_plan_node(state: RecoveryState) -> RecoveryState:
    """
    Generates a plan to recover the corrupted partitions.
    """
    if "messages" not in state:
        state["messages"] = []
        
    state["messages"].append(
        AIMessage(content="🛠️ Generating recovery plan...")
    )
    
    # Placeholder for recovery plan generation
    state["recovery_plan"] = "Run testdisk on partition_1 to recover the boot sector"
    
    state["messages"].append(
        AIMessage(content=f"📋 Recovery Plan:\n{state['recovery_plan']}\n\nDo you approve this recovery plan? Please respond with 'yes' to proceed or 'no' to cancel.")
    )
    
    return state


def human_in_the_loop_node(state: RecoveryState) -> RecoveryState:
    """
    Asks for human approval via chat. This node just asks - processing happens after interrupt.
    """
    if "messages" not in state:
        state["messages"] = []
    
    # Only ask if we haven't asked yet and don't have approval decision
    if state.get("human_approval") is None:
        state["messages"].append(
            AIMessage(content=f"📋 Recovery Plan:\n{state.get('recovery_plan', 'No plan generated')}\n\nDo you approve this recovery plan? Please respond with 'yes' to proceed or 'no' to cancel.")
        )
        # Mark that we're waiting for approval
        state["awaiting_approval"] = True
    
    return state


def process_approval_node(state: RecoveryState) -> RecoveryState:
    """
    Processes human approval from chat after interrupt.
    """
    if "messages" not in state:
        state["messages"] = []
        
    if state.get("messages"):
        # Look for the most recent human message
        for message in reversed(state["messages"]):
            if isinstance(message, HumanMessage):
                user_response = message.content.strip().lower()
                state["human_approval"] = user_response in ["yes", "y", "approve", "approved"]
                
                if state["human_approval"]:
                    state["messages"].append(
                        AIMessage(content="✅ Recovery plan approved. Proceeding with execution...")
                    )
                else:
                    state["messages"].append(
                        AIMessage(content="❌ Recovery plan rejected. Operation cancelled for safety.")
                    )
                break
    
    return state


def execute_recovery_plan_node(state: RecoveryState) -> RecoveryState:
    """
    Executes the recovery plan.
    """
    if "messages" not in state:
        state["messages"] = []
        
    state["messages"].append(
        AIMessage(content="🚀 Executing recovery plan...")
    )
    
    # Placeholder for executing the recovery plan
    state["messages"].append(
        AIMessage(content="✅ Recovery complete! Your data has been safely recovered.")
    )
    
    return state
