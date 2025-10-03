
from reactivex import throw
from typing import Literal, Tuple, List

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import BaseTool

RoleType = Literal["engineer_react_frontend", "engineer_react_backend", "engineer_react_fullstack"]

async def get_code_memory_tools(role: RoleType = None) -> List[BaseTool] | Tuple[List[BaseTool], List[BaseTool], List[BaseTool]]:
    mcp_client = MultiServerMCPClient(
        {
            "engineer_react_frontend_code_tools": {
                "url": "http://192.168.0.51:12008/metamcp/engineer-frontend-typescript/mcp",
                "transport": "streamable_http"
            },
            "engineer_react_backend_code_tools": {
                "url": "http://192.168.0.51:12008/metamcp/engineer-backend-typescript/mcp",
                "transport": "streamable_http"
            },
            "engineer_react_fullstack_code_tools": {
                "url": "http://192.168.0.51:12008/metamcp/engineer-fullstack-typescript/mcp",
                "transport": "streamable_http"
            }
        }
    )
    
    if role == "engineer_react_frontend":
        return await mcp_client.get_tools(server_name="engineer_react_frontend_code_tools")
    elif role == "engineer_react_backend":
        return await mcp_client.get_tools(server_name="engineer_react_backend_code_tools")
    elif role == "engineer_react_fullstack":
        return await mcp_client.get_tools(server_name="engineer_react_fullstack_code_tools")
    else:
        throw(ValueError("Role must be one of 'engineer_react_frontend', 'engineer_react_backend', or 'engineer_react_fullstack'."))
