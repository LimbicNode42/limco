from langchain.chat_models import init_chat_model
from typing import Literal

ModelType = Literal["sonnet_4", "sonnet_3_5", "opus_4"]

def get_anthropic_model(model: ModelType = "sonnet_4"):
    models = {
        "sonnet_4": "claude-sonnet-4-20250514",
        "sonnet_3_5": "claude-3-5-sonnet-20241022",
        "opus_4": "claude-opus-4-20250514"
    }
    
    if model not in models:
        raise ValueError(f"Model must be one of {list(models.keys())}")
    
    return init_chat_model(
        models[model],
        temperature=0.2,
    )
