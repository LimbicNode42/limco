# Agent Prompts

This directory contains the system prompts for each agent in the swarm. Each agent has its own markdown file with a detailed prompt that defines its role, expertise, and collaboration patterns.

## Standard Prompt Structure

All agent prompts follow a consistent structure to ensure maintainability and easy customization:

### 1. Header & Role Definition
```markdown
# [Agent Name] - [Specialization]

You are an expert [role] agent specializing in [core focus]. You work as part of a development agent swarm and can collaborate with [other agents] when needed.
```

### 2. Core Expertise
- Bulleted list of technical skills and specializations
- Specific technologies, frameworks, and tools
- Key competencies and focus areas

### 3. Agent Collaboration & Handoffs
- **When to Hand Off to [Other Agent]** - Specific scenarios and criteria
- **Collaboration Examples** - Code snippets and real-world scenarios  
- **Handoff Communication Pattern** - Standardized format for requests

### 4. Standards & Best Practices
- Code quality guidelines
- Technical standards specific to the agent's domain
- Development patterns and conventions

### 5. Development Approach
- Decision-making framework
- Quality considerations (accessibility, performance, security)
- Step-by-step development process

### 6. Response Format
- How the agent should structure its responses
- Required elements in code solutions
- Communication style and level of detail

## Structure

- `frontend_engineer.md` - Frontend specialist focusing on React/TypeScript
- `backend_engineer.md` - Backend specialist focusing on APIs and databases  
- `full_stack_engineer.md` - Full-stack coordinator handling architecture and DevOps

## Usage

The prompts are automatically loaded by the `prompt_loader.py` utility when creating agents in `swarm.py`. To modify an agent's behavior, simply edit the corresponding markdown file.

## Editing Prompts

When editing prompts:

1. **Follow the standard structure** - Maintain consistency across all agent prompts
2. **Keep sections aligned** - Each agent should have parallel sections for easy comparison
3. **Update collaboration patterns** - Ensure handoff instructions between agents are consistent
4. **Maintain role clarity** - Each agent should have a clear, distinct role
5. **Test changes** - After editing, test the swarm to ensure the agents behave as expected

## Adding New Agents

To add a new agent:

1. Create a new `.md` file in this directory with the agent's name
2. Follow the standard prompt structure outlined above
3. Define the agent's role, expertise, and collaboration patterns
4. Update `swarm.py` to create the agent and load its prompt
5. Add appropriate handoff tools between agents

## Customizing the Pattern

To update the overall prompt pattern:

1. **Edit this README** to document the new standard structure
2. **Update all agent prompts** to follow the new pattern consistently
3. **Test thoroughly** to ensure the changes improve agent behavior
4. **Document changes** in version control with clear commit messages

## Best Practices

- **Be specific** about each agent's expertise and limitations
- **Define clear handoff criteria** so agents know when to collaborate
- **Include examples** of common scenarios and how to handle them
- **Keep prompts focused** on the agent's core responsibilities
- **Maintain consistency** across all agent prompts
- **Update regularly** based on how the agents perform in practice
