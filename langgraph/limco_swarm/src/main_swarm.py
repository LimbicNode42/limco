import asyncio
import dotenv

from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_swarm

from prompt_loader import load_prompt
from models.anthropic import sonnet_4
from tools.agent_handoff import (
  handoff_to_frontend_engineer,
  handoff_to_backend_engineer,
  handoff_to_full_stack_engineer
)
from tools.code_memory import (
  engineer_react_frontend_code_tools,
  engineer_react_backend_code_tools,
  engineer_react_full_stack_code_tools
)

async def main():
    dotenv.load_dotenv()

    engineer_react_frontend = create_react_agent(
      name = "engineer_react_frontend",
      model = sonnet_4,
      tools=[
        handoff_to_backend_engineer,
        handoff_to_full_stack_engineer
      ] + engineer_react_frontend_code_tools,
      prompt=load_prompt("engineer_react_frontend")
    )

    engineer_react_backend = create_react_agent(
      name = "engineer_react_backend",
      model = sonnet_4,
      tools=[
        handoff_to_frontend_engineer,
        handoff_to_full_stack_engineer
      ] + engineer_react_backend_code_tools,
      prompt=load_prompt("engineer_react_backend")
    )

    engineer_react_full_stack = create_react_agent(
      name = "engineer_react_full_stack",
      model = sonnet_4,
      tools=[
        handoff_to_frontend_engineer,
        handoff_to_backend_engineer
      ] + engineer_react_full_stack_code_tools,
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