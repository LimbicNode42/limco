# Agentic Solutions Playground

A comprehensive playground for exploring and experimenting with various agentic AI frameworks and solutions.

## 🎯 Purpose

This repository serves as a testing ground and showcase for different agentic AI frameworks, allowing for easy comparison and experimentation with various approaches to autonomous AI systems.

## 🏗️ Directory Structure

```
limco/  (Agentic Solutions Playground)
├── crewai/          # CrewAI-based projects
│   └── coding_team/ # Autonomous software development company
├── langgraph/       # LangGraph-based projects
├── autogen/         # AutoGen-based projects
├── swarm/           # OpenAI Swarm-based projects
└── README.md        # This file
```

## 🚀 Current Projects

### CrewAI Framework

#### **Coding Team** (`crewai/coding_team/`)
An AI-powered autonomous software development company that can take high-level business goals and autonomously plan, analyze, and provide comprehensive project proposals.

**Features:**
- 10-agent development team with specialized roles
- Optimized model assignment (Claude Sonnet 4, Claude 3.7 Sonnet, Gemini 2.5 Flash)
- Comprehensive project analysis and implementation planning
- Rate limiting and cost optimization

**Quick Start:**
```bash
cd crewai/coding_team
pip install -e .

# Set up .env with API keys
python -m limco.main run "Your project goal here"
```

## � Planned Frameworks

### LangGraph
- **Coming Soon**: Workflow-based agentic solutions
- Focus: Complex multi-step reasoning and state management

### AutoGen
- **Coming Soon**: Multi-agent conversation frameworks
- Focus: Collaborative agent interactions and code generation

### OpenAI Swarm
- **Coming Soon**: Lightweight multi-agent orchestration
- Focus: Simple, scalable agent coordination

## 🛠️ Getting Started

### Prerequisites
- Python 3.10+
- API keys for various AI services (OpenAI, Anthropic, Google, etc.)

### Exploring Projects
1. **Browse the framework directories** to see available projects
2. **Navigate to a specific project** to see its README and setup instructions
3. **Install dependencies** for the framework you want to try
4. **Set up environment variables** as required by each project
5. **Run the examples** to see the agents in action

### Contributing New Projects
1. **Choose a framework directory** (or create a new one)
2. **Create a project subdirectory** with a descriptive name
3. **Include proper documentation** (README, setup instructions)
4. **Add examples** demonstrating the capabilities
5. **Update this main README** to reference your project

## 📁 Project Template Structure

Each project should follow this structure:
```
framework/
└── project_name/
    ├── src/                 # Source code
    ├── tests/              # Test files
    ├── docs/               # Documentation
    ├── examples/           # Usage examples
    ├── README.md           # Project-specific documentation
    ├── pyproject.toml      # Dependencies and configuration
    └── .env.example        # Environment variables template
```

## 🎯 Goals

- **Framework Comparison**: Easy side-by-side comparison of different agentic approaches
- **Best Practices**: Showcase optimal patterns for each framework
- **Learning Resource**: Educational examples for understanding agentic AI
- **Rapid Prototyping**: Quick setup for new agentic experiments

## � Resources

- [CrewAI Documentation](https://docs.crewai.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [OpenAI Swarm](https://github.com/openai/swarm)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch for your framework/project
3. Add your agentic solution following the project template
4. Update documentation
5. Submit a pull request

---

**Happy experimenting with agentic AI!** 🤖✨