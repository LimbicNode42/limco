# Agent Prompts

This directory contains the system prompts for each agent in the swarm. Each agent has its own markdown file with a detailed prompt that defines its role, expertise, and collaboration patterns.

## Structure

- `frontend_engineer.md` - Frontend specialist focusing on React/TypeScript
- `backend_engineer.md` - Backend specialist focusing on APIs and databases  
- `full_stack_engineer.md` - Full-stack coordinator handling architecture and DevOps

## Usage

The prompts are automatically loaded by the `prompt_loader.py` utility when creating agents in `swarm.py`. To modify an agent's behavior, simply edit the corresponding markdown file.

## Editing Prompts

When editing prompts:

1. **Keep the markdown structure** - The prompts use markdown formatting for clarity
2. **Maintain agent roles** - Each agent should have a clear, distinct role
3. **Update collaboration patterns** - Ensure handoff instructions between agents are consistent
4. **Test changes** - After editing, test the swarm to ensure the agents behave as expected

## Adding New Agents

To add a new agent:

1. Create a new `.md` file in this directory with the agent's name
2. Define the agent's role, expertise, and collaboration patterns
3. Update `swarm.py` to create the agent and load its prompt
4. Add appropriate handoff tools between agents

## Best Practices

- **Be specific** about each agent's expertise and limitations
- **Define clear handoff criteria** so agents know when to collaborate
- **Include examples** of common scenarios and how to handle them
- **Keep prompts focused** on the agent's core responsibilities
- **Update regularly** based on how the agents perform in practice
