# MCP Tools for Development Team Agents

This directory contains Model Context Protocol (MCP) tools that enable secure, collaborative code development for headless agent environments. These tools provide comprehensive capabilities for code execution, analysis, and file operations.

## Overview

The MCP tools are designed for senior and QA engineers working in automated, headless environments where agents need to collaborate on code without human intervention. All tools follow the MCP standard for tool integration and provide both sandboxed and native execution options.

## Tool Categories

### 1. Code Execution and Sandboxing (`mcp_code_execution.py`)

Provides secure Python code execution capabilities with multiple execution environments:

**Core Components:**
- `MCPPythonExecutor`: Sandboxed execution via Deno/Pyodide WebAssembly
- `NativeSubprocessExecutor`: Local Python execution with security controls
- `VirtualEnvironmentManager`: Isolated Python environment management

**Available Tools:**
- `execute_python_code()`: Execute Python code with automatic fallback
- `execute_python_code_sandbox()`: Force sandboxed execution
- `create_virtual_environment()`: Create isolated Python environments
- `list_virtual_environments()`: List available environments
- `install_package_in_venv()`: Install packages in specific environments
- `get_python_environment_info()`: Get environment details

**Security Features:**
- WebAssembly sandboxing via Pyodide
- Process isolation with timeouts
- Output size limits to prevent memory issues
- Environment variable control
- Working directory restrictions

### 2. Code Analysis and Understanding (`mcp_code_analysis.py`)

Comprehensive code analysis using multiple approaches for deep understanding:

**Core Components:**
- `SerenaAnalyzer`: Language server-based semantic analysis
- `RepoMapperAnalyzer`: Repository structure and dependency mapping
- `PythonASTAnalyzer`: Native Python AST parsing and analysis
- `CodeComplexityMetrics`: Cyclomatic complexity and code quality metrics

**Available Tools:**
- `analyze_code_with_serena()`: Semantic analysis with language server
- `analyze_repository_structure()`: Full repository analysis with dependencies
- `analyze_python_code_ast()`: Python-specific AST analysis
- `find_symbol_definitions()`: Locate function, class, and variable definitions
- `get_code_complexity_metrics()`: Calculate complexity and quality metrics
- `extract_code_dependencies()`: Extract import dependencies

**Analysis Capabilities:**
- Symbol resolution and cross-references
- Dependency graph construction
- Complexity analysis (cyclomatic, nesting depth)
- Code quality metrics
- Import and module analysis
- Function and class extraction

### 3. File Operations and Project Management (`mcp_file_operations.py`)

Efficient file operations and project structure analysis:

**Core Components:**
- `FileScopeAnalyzer`: Project-wide file importance analysis
- `TextEditor`: Line-oriented efficient text editing
- `LanguageServerManager`: Language server integration management

**Available Tools:**
- `analyze_file_importance()`: Analyze file importance within projects
- `read_file_efficiently()`: Cached line-based file reading
- `edit_file_at_line()`: Precise line-based editing operations
- `edit_file_range()`: Multi-line editing operations
- `get_language_server_info()`: Available language server information
- `clear_file_cache()`: Memory management for file operations

**Project Analysis Features:**
- Dependency importance scoring
- File relationship mapping
- Language server integration
- Efficient caching for large codebases
- Line-oriented editing for precision

## Installation and Setup

### Dependencies

All MCP tools are designed to work with optional dependencies and graceful fallbacks:

```bash
# Core dependencies (required)
pip install requests pathlib

# Optional for enhanced functionality
pip install deno  # For sandboxed execution
pip install pylsp  # For Python language server support

# Language server dependencies (optional)
npm install -g typescript-language-server  # TypeScript/JavaScript
go install golang.org/x/tools/gopls@latest  # Go
cargo install rust-analyzer  # Rust
```

### MCP Server Setup (Optional)

For full MCP integration, you can set up the actual MCP servers:

```bash
# pydantic-ai/mcp-run-python (sandboxed execution)
git clone https://github.com/pydantic-ai/mcp-run-python
cd mcp-run-python
deno install

# oraios/serena (code analysis)
git clone https://github.com/oraios/serena
cd serena
npm install

# RepoMapper concepts are implemented natively
```

## Usage Examples

### Code Execution

```python
from dev_team.tools import execute_python_code

# Execute simple code
result = execute_python_code("""
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print([fibonacci(i) for i in range(10)])
""")

print(result["output"])  # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
```

### Code Analysis

```python
from dev_team.tools import analyze_python_code_ast, get_code_complexity_metrics

code = """
def complex_function(data):
    result = []
    for item in data:
        if isinstance(item, str):
            if len(item) > 5:
                result.append(item.upper())
            else:
                result.append(item.lower())
        elif isinstance(item, int):
            result.append(item * 2)
    return result
"""

# Analyze structure
analysis = analyze_python_code_ast(code)
print(f"Functions found: {len(analysis['functions'])}")

# Get complexity metrics
metrics = get_code_complexity_metrics(code)
print(f"Cyclomatic complexity: {metrics['cyclomatic_complexity']}")
```

### File Operations

```python
from dev_team.tools import read_file_efficiently, edit_file_at_line

# Read specific lines from large file
content = read_file_efficiently("large_file.py", start_line=100, end_line=150)

# Edit file precisely
edit_result = edit_file_at_line(
    "source.py",
    line_number=25,
    content="# Added by agent analysis\n",
    operation="insert"
)
```

### Project Analysis

```python
from dev_team.tools import analyze_file_importance, analyze_repository_structure

# Analyze project file importance
importance = analyze_file_importance("/path/to/project")
print("Most important files:")
for file_info in importance["important_files"][:5]:
    print(f"  {file_info['file_path']}: {file_info['importance_score']:.2f}")

# Full repository structure analysis
repo_analysis = analyze_repository_structure("/path/to/project")
print(f"Total files: {len(repo_analysis['files'])}")
print(f"Dependency relationships: {len(repo_analysis['dependencies'])}")
```

## Architecture and Design

### Execution Strategy

The tools implement a multi-tier execution strategy:

1. **Primary**: MCP server integration for standardized tool communication
2. **Fallback**: Native subprocess execution with security controls
3. **Caching**: Intelligent caching to reduce redundant operations
4. **Error Handling**: Comprehensive error handling with graceful degradation

### Security Model

- **Sandboxed Execution**: WebAssembly isolation via Pyodide
- **Process Isolation**: Subprocess execution with timeouts and limits
- **Input Validation**: Comprehensive input sanitization
- **Resource Limits**: Memory and time constraints
- **Environment Control**: Restricted environment variable access

### Performance Optimization

- **Lazy Loading**: Components loaded only when needed
- **Caching Strategy**: File content and analysis result caching
- **Parallel Processing**: Multi-threaded analysis where appropriate
- **Memory Management**: Automatic cleanup and cache eviction

## Testing

Comprehensive test suites are provided:

```bash
# Run unit tests
python -m pytest tests/unit_tests/test_mcp_*.py -v

# Run integration tests
python -m pytest tests/integration_tests/test_mcp_tools_integration.py -v

# Run specific tool tests
python -m pytest tests/unit_tests/test_mcp_code_execution.py::TestMCPPythonExecutor -v
```

## Error Handling and Debugging

All tools provide comprehensive error information:

```python
result = execute_python_code("invalid python syntax")
if not result["success"]:
    print(f"Error: {result['error']}")
    print(f"Execution method: {result['execution_method']}")
```

Common error scenarios and solutions:

- **MCP Server Unavailable**: Automatic fallback to native execution
- **Syntax Errors**: Detailed error reporting with line numbers
- **Resource Limits**: Clear timeout and memory limit messages
- **Permission Issues**: Environment and file access error details

## Integration with LangGraph

The tools are designed to integrate seamlessly with the existing LangGraph agent system:

```python
from dev_team.tools import get_all_tools

# Get all tools including MCP tools
all_tools = get_all_tools()

# Tools are automatically available to agents
agent = create_agent(tools=all_tools)
```

## Contributing

When adding new MCP tools:

1. Follow the existing patterns for error handling and fallbacks
2. Implement comprehensive unit and integration tests
3. Add tools to the `__init__.py` file for automatic discovery
4. Update this README with new functionality
5. Ensure graceful degradation when dependencies are unavailable

## Roadmap

Planned enhancements:

- [ ] Additional language server integrations (Java, C#, etc.)
- [ ] Enhanced dependency analysis with transitive dependencies
- [ ] Real-time code quality monitoring
- [ ] Integration with additional MCP servers
- [ ] Performance metrics and optimization
- [ ] Advanced refactoring capabilities

## Troubleshooting

### Common Issues

**MCP Server Connection Issues:**
```python
# Check if MCP servers are available
from dev_team.tools import get_language_server_info
servers = get_language_server_info()
print(f"Available servers: {servers}")
```

**Memory Issues with Large Projects:**
```python
# Clear caches regularly
from dev_team.tools import clear_file_cache
clear_file_cache()  # Clear all file caches
```

**Execution Timeouts:**
- Increase timeout values in executor initialization
- Break large operations into smaller chunks
- Use background execution for long-running tasks

For additional support, see the troubleshooting guides in the docs/ directory.
