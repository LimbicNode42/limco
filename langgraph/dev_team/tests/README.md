# Test Organization

This directory contains comprehensive tests for the development team project, organized into a clear hierarchy for better maintainability.

## Structure

```
tests/
├── conftest.py                          # Shared test configuration and fixtures
├── unit_tests/                          # Unit tests for individual components
│   ├── core/                           # Core system component tests
│   │   ├── test_complexity_analyzer.py  # Code complexity analysis
│   │   ├── test_configuration.py        # System configuration
│   │   ├── test_human_assistance.py     # Human-in-the-loop assistance
│   │   └── test_states.py              # State management
│   └── tools/                          # Tool-specific unit tests
│       ├── test_code_review_tools.py    # Code review and quality tools
│       ├── test_github_mcp.py          # GitHub MCP integration
│       ├── test_github_mcp_simple.py   # Simplified GitHub MCP tests
│       ├── test_github_tools.py        # GitHub tool functionality
│       ├── test_human_in_loop_tools.py # Human interaction tools
│       └── test_web_search_tools.py    # Web search functionality
└── integration_tests/                  # Integration and end-to-end tests
    ├── tools/                          # Tool integration tests
    │   ├── test_code_review_integration.py  # Code review workflow integration
    │   ├── test_github_integration.py       # GitHub workflow integration
    │   ├── test_github_mcp_integration.py   # GitHub MCP integration tests
    │   └── test_web_search_integration.py   # Web search integration tests
    └── workflows/                      # Complete workflow tests
        ├── test_graph.py               # Graph execution and routing
        └── test_human_assistance_workflow.py # Human assistance workflows
```

## Running Tests

### All Tests
```bash
python -m pytest tests/
```

### Unit Tests Only
```bash
python -m pytest tests/unit_tests/
```

### Integration Tests Only
```bash
python -m pytest tests/integration_tests/
```

### Specific Categories
```bash
# Core component tests
python -m pytest tests/unit_tests/core/

# Tool tests
python -m pytest tests/unit_tests/tools/

# Tool integration tests
python -m pytest tests/integration_tests/tools/

# Workflow tests
python -m pytest tests/integration_tests/workflows/
```

### Individual Test Files
```bash
# Code review tools
python -m pytest tests/unit_tests/tools/test_code_review_tools.py

# GitHub integration
python -m pytest tests/integration_tests/tools/test_github_integration.py

# Complete workflows
python -m pytest tests/integration_tests/workflows/test_graph.py
```

## Test Categories

### Unit Tests (tests/unit_tests/)
- **Core**: System components (configuration, states, complexity analysis)
- **Tools**: Individual tool functionality (code review, GitHub, web search)

### Integration Tests (tests/integration_tests/)
- **Tools**: Tool integration and workflow testing
- **Workflows**: Complete end-to-end workflow validation

## Best Practices

1. **Unit tests** should test individual functions and classes in isolation
2. **Integration tests** should test how components work together
3. **Workflow tests** should test complete user scenarios
4. Use meaningful test names that describe what is being tested
5. Include both positive and negative test cases
6. Mock external dependencies in unit tests
7. Use real integrations in integration tests when possible

## Coverage

Run with coverage to ensure comprehensive testing:
```bash
python -m pytest tests/ --cov=src/ --cov-report=html
```
