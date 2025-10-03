from langgraph_swarm import create_handoff_tool

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