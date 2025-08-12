# MCP QA & Testing Tools

This module provides comprehensive Quality Assurance and Testing capabilities for the development team agents using Model Context Protocol (MCP) tools.

## Overview

The QA tools integrate two powerful MCP servers to provide:

1. **Code Quality Analysis** - Using [hyperb1iss/lucidity-mcp](https://github.com/hyperb1iss/lucidity-mcp)
2. **Load Testing** - Using [QAInsights/locust-mcp-server](https://github.com/QAInsights/locust-mcp-server)

## Tools Available

### Code Quality Analysis

#### `analyze_code_quality`
Comprehensive code quality analysis across 10 critical dimensions:

- **Unnecessary Complexity** - Overly complex algorithms and abstractions
- **Poor Abstractions** - Leaky or inappropriate abstractions
- **Unintended Code Deletion** - Accidental removal of critical functionality
- **Hallucinated Components** - References to non-existent functions/APIs
- **Style Inconsistencies** - Deviations from coding standards
- **Security Vulnerabilities** - Potential security issues
- **Performance Issues** - Inefficient algorithms or operations
- **Code Duplication** - Repeated logic that should be refactored
- **Incomplete Error Handling** - Missing exception handling
- **Test Coverage Gaps** - Missing tests for critical functionality

**Parameters:**
- `workspace_root`: Root directory of the workspace/repository
- `target_path`: Optional specific file/directory to analyze
- `focus_dimensions`: Optional list of specific quality dimensions to focus on

**Example:**
```python
result = analyze_code_quality(
    "/path/to/project",
    focus_dimensions=["security_vulnerabilities", "performance_issues"]
)
```

### Load Testing

#### `run_load_test`
Execute load tests using Locust for performance testing.

**Parameters:**
- `test_file`: Path to Locust test file (.py)
- `target_host`: Target host URL to test
- `users`: Number of concurrent users to simulate
- `spawn_rate`: Rate at which users are spawned per second  
- `runtime`: Test duration (e.g., "30s", "2m", "1h")
- `headless`: Run in headless mode (True) or with UI (False)

**Example:**
```python
result = run_load_test(
    "test_api.py",
    "http://api.example.com",
    users=50,
    spawn_rate=5,
    runtime="2m"
)
```

#### `create_load_test_script`
Generate Locust test scripts for specified targets and endpoints.

**Parameters:**
- `target_url`: Base URL of the target application
- `test_name`: Name for the test class
- `endpoints`: List of endpoint paths to test

**Example:**
```python
result = create_load_test_script(
    "http://api.example.com",
    "api_performance_test",
    ["/users", "/orders", "/health", "/metrics"]
)
```

### Environment Validation

#### `validate_test_environment`
Validate testing environment and dependencies.

**Parameters:**
- `workspace_root`: Root directory of the workspace
- `target_url`: Optional target URL to check connectivity

**Example:**
```python
result = validate_test_environment(
    "/path/to/project",
    "http://api.example.com"
)
```

## Installation & Setup

### Prerequisites

1. **Python 3.13+**
2. **Git** (for code change analysis)
3. **Optional: Lucidity MCP Server**
   ```bash
   git clone https://github.com/hyperb1iss/lucidity-mcp.git
   cd lucidity-mcp
   uv venv .venv
   source .venv/bin/activate
   uv sync
   ```

4. **Optional: Locust** (for load testing)
   ```bash
   pip install locust
   ```

### Usage Patterns

#### Comprehensive Code Review
```python
# Analyze all quality dimensions
quality_result = analyze_code_quality("/path/to/project")

# Focus on security and performance
security_result = analyze_code_quality(
    "/path/to/project",
    focus_dimensions=["security_vulnerabilities", "performance_issues"]
)
```

#### Performance Testing Workflow
```python
# 1. Create test script
script_result = create_load_test_script(
    "http://api.example.com",
    "api_test",
    ["/api/users", "/api/orders", "/health"]
)

# 2. Run load test
if script_result["success"]:
    test_result = run_load_test(
        script_result["test_file_path"],
        "http://api.example.com",
        users=25,
        runtime="1m"
    )
    
    # 3. Analyze results
    if test_result["success"]:
        print(f"Success Rate: {test_result['performance_summary']['success_rate']}%")
        print(f"RPS: {test_result['performance_summary']['requests_per_second']}")
```

#### Environment Validation
```python
# Validate environment before testing
env_result = validate_test_environment(
    "/path/to/project",
    "http://target-api.com"
)

if env_result["overall_status"] == "ready":
    print("Environment ready for testing!")
else:
    print("Setup needed:", env_result["recommendations"])
```

## Quality Analysis Dimensions

### Security Focus
```python
analyze_code_quality(project_path, focus_dimensions=[
    "security_vulnerabilities",
    "incomplete_error_handling"
])
```

### Performance Focus  
```python
analyze_code_quality(project_path, focus_dimensions=[
    "performance_issues",
    "unnecessary_complexity"
])
```

### Maintainability Focus
```python
analyze_code_quality(project_path, focus_dimensions=[
    "code_duplication", 
    "poor_abstractions",
    "style_inconsistencies"
])
```

## Native Fallbacks

The tools include native fallback implementations when MCP servers are unavailable:

- **Code Analysis**: Pattern-based analysis for common issues
- **Load Testing**: Direct Locust command execution
- **Git Integration**: Native git commands for change detection

## Error Handling

All tools include comprehensive error handling:

- Graceful degradation when external services unavailable
- Detailed error messages for troubleshooting
- Timeout protection for long-running operations
- Input validation and sanitization

## Integration with LangGraph

The QA tools are designed for seamless integration with LangGraph agents:

```python
from dev_team.tools import get_all_tools

# Get all tools including QA tools
tools = get_all_tools()

# QA tools are automatically included:
# - analyze_code_quality
# - run_load_test  
# - create_load_test_script
# - validate_test_environment
```

## Testing

Comprehensive test coverage includes:

- Unit tests for all tool functions
- Integration tests for workflow scenarios
- Error handling and edge case testing
- Concurrent operation testing
- Environment validation testing

Run tests:
```bash
pytest tests/unit_tests/test_mcp_qa_*.py -v
pytest tests/integration_tests/test_mcp_qa_*.py -v
```

## Example Workflows

### Pre-commit Quality Check
```python
# Before committing code
env_check = validate_test_environment(project_path)
if env_check["validation_results"]["git_repository"]:
    quality_result = analyze_code_quality(project_path)
    
    if quality_result["success"]:
        issues = quality_result["analysis"].get("total_issues", 0)
        print(f"Found {issues} quality issues")
```

### API Performance Validation
```python
# Test API performance after deployment
test_script = create_load_test_script(
    "https://api.production.com",
    "production_test",
    ["/health", "/api/v1/users", "/api/v1/metrics"]
)

load_result = run_load_test(
    test_script["test_file_path"],
    "https://api.production.com", 
    users=100,
    runtime="5m"
)

if load_result["performance_summary"]["success_rate"] < 99:
    print("⚠️  Performance degradation detected!")
```

## Best Practices

1. **Regular Quality Checks**: Run code analysis before major commits
2. **Performance Baselines**: Establish performance benchmarks for APIs
3. **Focused Analysis**: Use dimension filtering for specific concerns
4. **Environment Validation**: Always validate setup before testing
5. **Incremental Testing**: Start with low load and scale up gradually

## Troubleshooting

### Common Issues

1. **Lucidity Not Available**: Tools fall back to pattern-based analysis
2. **Locust Not Installed**: Install with `pip install locust`
3. **Git Not Found**: Install Git for change analysis features
4. **Permission Errors**: Ensure write permissions for temporary files

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```
