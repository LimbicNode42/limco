from langchain.chat_models import init_chat_model

sonnet_4 = init_chat_model(
  "claude-sonnet-4-20250514",
  temperature=0.2,
)