# OpenAI Swarm Projects

This directory contains projects built using OpenAI's Swarm framework for lightweight multi-agent orchestration.

## About OpenAI Swarm

Swarm is an experimental framework for building lightweight multi-agent systems. It focuses on making agent coordination and handoffs as natural and lightweight as possible.

## Key Features

- **Lightweight**: Minimal overhead for agent coordination
- **Simple Handoffs**: Easy agent-to-agent handoffs
- **Function Calling**: Natural integration with function calling
- **Flexible Orchestration**: Dynamic agent selection and routing
- **Minimal Abstraction**: Close to the underlying LLM capabilities

## Coming Soon

We'll be adding Swarm-based projects that showcase:
- Dynamic agent routing
- Lightweight multi-agent coordination
- Function-based agent interactions
- Scalable agent orchestration

## Resources

- [OpenAI Swarm GitHub](https://github.com/openai/swarm)
- [Swarm Documentation](https://github.com/openai/swarm/blob/main/README.md)
- [Swarm Examples](https://github.com/openai/swarm/tree/main/examples)

## Project Template

When creating a new Swarm project, follow this structure:
```
project_name/
├── src/
│   ├── agents/          # Agent definitions
│   ├── functions/       # Agent functions
│   ├── orchestration/   # Orchestration logic
│   └── main.py          # Entry point
├── tests/
├── docs/
├── examples/
├── README.md
├── pyproject.toml
└── .env.example
```
