import asyncio
import dotenv

from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_swarm

from prompt_loader import load_prompt
from models.anthropic import get_anthropic_model
from tools.agent_handoff import get_handoff_tool, get_all_handoff_tools
from tools.code_memory import get_code_memory_tools

async def main():
    dotenv.load_dotenv()

    engineer_react_frontend = create_react_agent(
      name = "engineer_react_frontend",
      model = get_anthropic_model("sonnet_4"),
      tools=[
         get_handoff_tool("engineer_react_backend"), 
         get_handoff_tool("engineer_react_fullstack")
      ] + get_code_memory_tools(role="engineer_react_frontend"),
      prompt=load_prompt("engineer_react_frontend")
    )

    engineer_react_backend = create_react_agent(
      name = "engineer_react_backend",
      model = get_anthropic_model("sonnet_4"),
      tools=[
        get_handoff_tool("engineer_react_frontend"),
        get_handoff_tool("engineer_react_fullstack")
      ] + get_code_memory_tools(role="engineer_react_backend"),
      prompt=load_prompt("engineer_react_backend")
    )

    engineer_react_full_stack = create_react_agent(
      name = "engineer_react_full_stack",
      model = get_anthropic_model("sonnet_4"),
      tools=[
        get_handoff_tool("engineer_react_frontend"),
        get_handoff_tool("engineer_react_backend")
      ] + get_code_memory_tools(role="engineer_react_full_stack"),
      prompt=load_prompt("engineer_react_full_stack")
    )

    engineering_team = create_swarm(
      agents=[
        engineer_react_frontend,
        engineer_react_backend,
        engineer_react_full_stack
      ],
      default_active_agent="engineer_react_full_stack",
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