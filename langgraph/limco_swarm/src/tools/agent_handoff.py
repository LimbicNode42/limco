from langgraph_swarm import create_handoff_tool
from typing import Literal, List

AgentRole = Literal["engineer_react_frontend", "engineer_react_backend", "engineer_react_fullstack"]

def get_handoff_tool(role: AgentRole) -> object:
    handoff_configs = {
        "engineer_react_frontend": {
            "name": "handoff_to_engineer_react_frontend",
            "agent_name": "engineer_react_frontend",
            "description": "Handoff work to engineer_react_frontend or ask a engineer_react_frontend for help"
        },
        "engineer_react_backend": {
            "name": "handoff_to_engineer_react_backend",
            "agent_name": "engineer_react_backend",
            "description": "Handoff work to engineer_react_backend or ask a engineer_react_backend for help"
        },
        "engineer_react_fullstack": {
            "name": "handoff_to_engineer_react_fullstack",
            "agent_name": "engineer_react_fullstack",
            "description": "Handoff work to engineer_react_fullstack or ask a engineer_react_fullstack for help"
        }
    }
    
    if role not in handoff_configs:
        raise ValueError(f"Role must be one of {list(handoff_configs.keys())}")
    
    config = handoff_configs[role]
    return create_handoff_tool(
        name=config["name"],
        agent_name=config["agent_name"],
        description=config["description"]
    )

def get_all_handoff_tools(exclude_role: AgentRole = None) -> List[object]:
    all_roles = ["engineer_react_frontend", "engineer_react_backend", "engineer_react_fullstack"]

    if exclude_role:
        roles_to_include = [role for role in all_roles if role != exclude_role]
    else:
        roles_to_include = all_roles
    
    return [get_handoff_tool(role) for role in roles_to_include]
