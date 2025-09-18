import asyncio
import dotenv
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_swarm, create_handoff_tool
from langchain_mcp_adapters.client import MultiServerMCPClient

from prompt_loader import load_prompt

# Set up environment variables for Claude API
# You can also set ANTHROPIC_API_KEY environment variable instead
# os.environ["ANTHROPIC_API_KEY"] = "your-api-key-here"

async def main():
    dotenv.load_dotenv()

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
        },
        "backend_engineer": {
          "url" : "http://192.168.0.51:12008/metamcp/engineer-backend-typescript/mcp",
          "transport" : "streamable_http"
        },
        "full_stack_engineer": {
          "url" : "http://192.168.0.51:12008/metamcp/engineer-fullstack-typescript/mcp",
          "transport" : "streamable_http"
        }
      }
    )
    frontend_engineer_mcp_tools = await mcp_client.get_tools(server_name="frontend_engineer")
    backend_engineer_mcp_tools = await mcp_client.get_tools(server_name="backend_engineer")
    full_stack_engineer_mcp_tools = await mcp_client.get_tools(server_name="full_stack_engineer")

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
      ] + backend_engineer_mcp_tools,
      prompt=load_prompt("backend_engineer")
    )
    full_stack_engineer = create_react_agent(
      name = "full_stack_engineer",
      model = sonnet_4,
      tools=[
        handoff_to_frontend_engineer,
        handoff_to_backend_engineer
      ] + full_stack_engineer_mcp_tools,
      prompt=load_prompt("full_stack_engineer")
    )

    engineering_team = create_swarm(
      agents=[
        frontend_engineer,
        backend_engineer,
        full_stack_engineer
      ],
      default_active_agent="full_stack_engineer",
    ).compile()

    return engineering_team

if __name__ == "__main__":
    engineering_team = asyncio.run(main())

    for chunk in engineering_team.stream(
      {
          "messages": [
              {
                  "role": "user",
                  "content": "Create a simple web app with a button that says Click Me and when clicked shows an alert that says Hello World"
              }
          ]
      }
    ):
      print(chunk)
      print("\n")