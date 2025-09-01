from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_swarm, create_handoff_tool
from .prompt_loader import load_prompt

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
  ],
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
  ]
)

engineering_team.compile()