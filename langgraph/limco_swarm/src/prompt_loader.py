"""Utility functions for loading agent prompts from files."""

import os
from pathlib import Path


def load_prompt(agent_name: str) -> str:
    """Load prompt content for a specific agent from the prompts directory.
    
    Args:
        agent_name: Name of the agent (e.g., 'frontend_engineer')
        
    Returns:
        The prompt content as a string
        
    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    # Get the directory where this module is located
    current_dir = Path(__file__).parent
    prompt_file = current_dir / "prompts" / f"{agent_name}.md"
    
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        return f.read().strip()


def load_all_prompts() -> dict[str, str]:
    """Load all available agent prompts.
    
    Returns:
        Dictionary mapping agent names to their prompt content
    """
    current_dir = Path(__file__).parent
    prompts_dir = current_dir / "prompts"
    prompts = {}
    
    if not prompts_dir.exists():
        return prompts
    
    for prompt_file in prompts_dir.glob("*.md"):
        agent_name = prompt_file.stem
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompts[agent_name] = f.read().strip()
    
    return prompts
