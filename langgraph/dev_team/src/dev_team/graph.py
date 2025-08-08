"""LangGraph single-node graph template.

Returns a predefined response. Replace logic and configuration as needed.
"""

from __future__ import annotations

from typing import Any, Dict, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph

# Add current directory to path to find goals module
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import goals

class Configuration(TypedDict):
    """Configurable parameters for the agent.

    Set these when creating assistants OR when invoking the graph.
    See: https://langchain-ai.github.io/langgraph/cloud/how-tos/configuration_cloud/
    """

    my_configurable_param: str


async def founder(state: goals.Vision, config: RunnableConfig) -> Dict[str, Any]:
    """Process input and returns output.

    Can use runtime configuration to alter behavior.
    """
    configuration = config["configurable"]
    return {
        "changeme": "output from call_model. "
        f'Configured with {configuration.get("my_configurable_param")}'
    }

async def cto(state: goals.TechnologyStrategy, config: RunnableConfig) -> Dict[str, Any]:
    """Process input and returns output.

    Can use runtime configuration to alter behavior.
    """
    configuration = config["configurable"]
    return {
        "changeme": "output from call_model. "
        f'Configured with {configuration.get("my_configurable_param")}'
    }

async def engineering_manager(state: goals.TechnologyIteration, config: RunnableConfig) -> Dict[str, Any]:
    """Process input and returns output.

    Can use runtime configuration to alter behavior.
    """
    configuration = config["configurable"]
    return {
        "changeme": "output from call_model. "
        f'Configured with {configuration.get("my_configurable_param")}'
    }

async def senior_engineer(state: goals.TechnologyTask, config: RunnableConfig) -> Dict[str, Any]:
    """Process input and returns output.

    Can use runtime configuration to alter behavior.
    """
    configuration = config["configurable"]
    return {
        "changeme": "output from call_model. "
        f'Configured with {configuration.get("my_configurable_param")}'
    }

# Define the graph
graph = (
    StateGraph(goals.State, config_schema=Configuration)
    .add_node(founder)
    .add_node(cto)
    .add_node(engineering_manager)
    .add_node(senior_engineer)
    .add_edge("__start__", "founder")
    .add_edge("founder", "cto")
    .add_edge("cto", "engineering_manager")
    .add_edge("engineering_manager", "senior_engineer")
    .compile(name="Dev Team 1")
)
