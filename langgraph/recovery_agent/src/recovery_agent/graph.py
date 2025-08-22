from langgraph.graph import StateGraph, END
from .states import RecoveryState
from .nodes import (
    detect_drives_node,
    select_drive_node,
    process_drive_selection_node,
    clone_drive_node,
    analyze_partitions_node,
    generate_recovery_plan_node,
    execute_recovery_plan_node,
    human_in_the_loop_node,
    process_approval_node,
)
from .edges import (
    drive_selection_edge,
    clone_drive_edge,
    analyze_partitions_edge,
    generate_recovery_plan_edge,
    execute_recovery_plan_edge,
)


def create_recovery_graph():
    """
    Creates the state graph for the data recovery agent.
    """
    workflow = StateGraph(RecoveryState)

    # Add nodes
    workflow.add_node("detect_drives", detect_drives_node)
    workflow.add_node("select_drive", select_drive_node)
    workflow.add_node("process_drive_selection", process_drive_selection_node)
    workflow.add_node("clone_drive", clone_drive_node)
    workflow.add_node("analyze_partitions", analyze_partitions_node)
    workflow.add_node("generate_recovery_plan", generate_recovery_plan_node)
    workflow.add_node("human_in_the_loop", human_in_the_loop_node)
    workflow.add_node("process_approval", process_approval_node)
    workflow.add_node("execute_recovery_plan", execute_recovery_plan_node)

    # Set entry point
    workflow.set_entry_point("detect_drives")

    # Add edges
    workflow.add_edge("detect_drives", "select_drive")
    workflow.add_edge("select_drive", "process_drive_selection")
    workflow.add_conditional_edges(
        "process_drive_selection",
        drive_selection_edge,
        {
            "clone_drive": "clone_drive",
            "__end__": END,
        },
    )
    workflow.add_conditional_edges(
        "clone_drive",
        clone_drive_edge,
        {
            "analyze_partitions": "analyze_partitions",
            "__end__": END,
        },
    )
    workflow.add_conditional_edges(
        "analyze_partitions",
        analyze_partitions_edge,
        {
            "generate_recovery_plan": "generate_recovery_plan",
            "__end__": END,
        },
    )
    workflow.add_conditional_edges(
        "generate_recovery_plan",
        generate_recovery_plan_edge,
        {
            "human_in_the_loop": "human_in_the_loop",
            "__end__": END,
        },
    )
    workflow.add_edge("human_in_the_loop", "process_approval")
    workflow.add_conditional_edges(
        "process_approval",
        execute_recovery_plan_edge,
        {
            "execute_recovery_plan": "execute_recovery_plan",
            "__end__": END,
        },
    )
    workflow.add_edge("execute_recovery_plan", END)

    return workflow.compile(
        interrupt_after=["select_drive", "human_in_the_loop"],
    )
