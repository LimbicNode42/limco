# CrewAI Projects

This directory contains projects built using the CrewAI framework for orchestrating role-playing, autonomous AI agents.

## About CrewAI

CrewAI is designed to facilitate the collaboration of role-playing AI agents. By fostering collaborative intelligence, CrewAI empowers agents to work together seamlessly, tackling complex tasks as a unified team.

## Key Features

- **Role-Based Agents**: Agents with specific roles and capabilities
- **Collaborative Intelligence**: Agents work together as a team
- **Task Orchestration**: Structured task execution and handoffs
- **Memory and Context**: Agents maintain context across interactions
- **Tool Integration**: Easy integration of external tools and APIs

## Current Projects

### Coding Team (`coding_team/`)

An AI-powered autonomous software development company that can take high-level business goals and autonomously plan, analyze, and provide comprehensive project proposals.

**Features:**
- 10-agent development team with specialized roles
- Optimized model assignment (Claude Sonnet 4, Claude 3.7 Sonnet, Gemini 2.5 Flash)
- Comprehensive project analysis and implementation planning
- Rate limiting and cost optimization

**Quick Start:**
```bash
cd coding_team
pip install -e .
# Set up .env with API keys
python -m limco.main run "Your project goal here"
```

## Resources

- [CrewAI Documentation](https://docs.crewai.com/)
- [CrewAI Examples](https://github.com/joaomdmoura/crewAI-examples)
- [CrewAI Tools](https://github.com/joaomdmoura/crewAI-tools)

## Project Template

When creating a new CrewAI project, follow this structure:
```
project_name/
├── src/
│   ├── project_name/
│   │   ├── config/      # Agent and task configurations
│   │   ├── tools/       # Custom tools
│   │   ├── utils/       # Utility functions
│   │   ├── crew.py      # Crew definition
│   │   └── main.py      # Entry point
├── tests/
├── docs/
├── examples/
├── README.md
├── pyproject.toml
└── .env.example
```
