from .states import RecoveryState


def drive_selection_edge(state: RecoveryState) -> str:
    """
    Determines which path to take after drive selection.
    """
    if state.get("selected_drive"):
        return "clone_drive"
    return "__end__"


def clone_drive_edge(state: RecoveryState) -> str:
    """
    Determines which path to take after cloning the drive.
    """
    if state.get("clone_path"):
        return "analyze_partitions"
    return "__end__"


def analyze_partitions_edge(state: RecoveryState) -> str:
    """
    Determines which path to take after analyzing partitions.
    """
    if state.get("analysis_results") and any(
        status == "corrupted" for status in state["analysis_results"].values()
    ):
        return "generate_recovery_plan"
    return "__end__"


def generate_recovery_plan_edge(state: RecoveryState) -> str:
    """

    Determines which path to take after generating the recovery plan.
    """
    if state.get("recovery_plan"):
        return "human_in_the_loop"
    return "__end__"


def execute_recovery_plan_edge(state: RecoveryState) -> str:
    """
    Determines which path to take after human approval.
    """
    if state.get("human_approval"):
        return "execute_recovery_plan"
    return "__end__"
