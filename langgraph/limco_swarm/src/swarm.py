import asyncio
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_swarm, create_handoff_tool
from langchain_mcp_adapters.client import MultiServerMCPClient

from prompt_loader import load_prompt

async def main():
    handoff_to_frontend_engineer = create_handoff_tool(
      name="handoff_to_frontend_engineer",
      agent_name="frontend_engineer",
      description="Handoff work to frontend_engineer or ask a frontend_engineer for help"
    )
    handoff_to_backend_engineer = create_handoff_tool(
      name="handoff_to_backend_engineer",
      agent_name="backend_engineer",
      description="Handoff work to backend_engineer or ask a backend_engineer for help"
    )
    handoff_to_full_stack_engineer = create_handoff_tool(
      name="handoff_to_full_stack_engineer",
      agent_name="full_stack_engineer",
      description="Handoff work to full_stack_engineer or ask a full_stack_engineer for help"
    )

    mcp_client = MultiServerMCPClient(
      {
        "frontend_engineer": {
          "url" : "http://192.168.0.51:12008/metamcp/engineer-frontend-typescript/mcp",
          "transport" : "streamable_http"
        }
      }
    )
    frontend_engineer_mcp_tools = await mcp_client.get_tools(server_name="frontend_engineer")
    print(f"Loaded {len(frontend_engineer_mcp_tools)} tools from MCP for frontend_engineer")

    sonnet_4 = init_chat_model(
      "claude-sonnet-4-20250514",
      temperature=0.2,
    )

    frontend_engineer = create_react_agent(
      name = "frontend_engineer",
      model = sonnet_4,
      tools=[
        handoff_to_backend_engineer,
        handoff_to_full_stack_engineer
      ] + frontend_engineer_mcp_tools,
      prompt=load_prompt("frontend_engineer")
    )
    backend_engineer = create_react_agent(
      name = "backend_engineer",
      model = sonnet_4,
      tools=[
        handoff_to_frontend_engineer,
        handoff_to_full_stack_engineer
      ],
      prompt=load_prompt("backend_engineer")
    )
    full_stack_engineer = create_react_agent(
      name = "full_stack_engineer",
      model = sonnet_4,
      tools=[
        handoff_to_frontend_engineer,
        handoff_to_backend_engineer
      ],
      prompt=load_prompt("full_stack_engineer")
    )

    engineering_team = create_swarm(
      agents=[
        frontend_engineer,
        backend_engineer,
        full_stack_engineer
      ],
      default_active_agent="full_stack_engineer",
    )

    engineering_team.compile()
    return engineering_team

if __name__ == "__main__":
    engineering_team = asyncio.run(main())