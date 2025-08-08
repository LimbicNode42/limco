# AutoGen Projects

This directory contains projects built using Microsoft's AutoGen framework for multi-agent conversation systems.

## About AutoGen

AutoGen is a framework that enables development of LLM applications using multiple agents that can converse with each other to solve tasks.

## Key Features

- **Multi-Agent Conversations**: Multiple agents can participate in conversations
- **Role-Based Agents**: Different agents can have specialized roles and capabilities
- **Code Generation**: Built-in support for code generation and execution
- **Human Interaction**: Seamless integration of human feedback
- **Customizable Workflows**: Flexible conversation patterns and workflows

## Coming Soon

We'll be adding AutoGen-based projects that showcase:
- Collaborative code generation
- Multi-agent problem solving
- Human-AI collaboration workflows
- Specialized agent teams

## Resources

- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [AutoGen Examples](https://github.com/microsoft/autogen/tree/main/notebook)
- [AutoGen Studio](https://microsoft.github.io/autogen/docs/topics/agentchat/autogen-studio)

## Project Template

When creating a new AutoGen project, follow this structure:
```
project_name/
├── src/
│   ├── agents/          # Agent definitions
│   ├── workflows/       # Conversation workflows
│   ├── tools/           # Custom tools and functions
│   └── main.py          # Entry point
├── tests/
├── docs/
├── examples/
├── README.md
├── pyproject.toml
└── .env.example
```
