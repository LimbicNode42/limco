# MCP QA Tools Implementation

## Overview

The MCP QA Tools provide comprehensive quality assurance and performance testing capabilities through a hybrid MCP (Model Context Protocol) connection strategy. This implementation follows the same comprehensive approach used for other MCP tools in the system.

## Architecture

### Hybrid Connection Strategy

The system implements a three-tier connection approach:

1. **Primary: MCP Aggregator Connection**
   - Connects to aggregators like MCPX or mcgravity
   - Provides centralized access to multiple MCP servers
   - Configurable endpoint: `MCP_AGGREGATOR_URL` (default: `http://localhost:8080`)

2. **Secondary: Individual MCP Server Startup**
   - Automatically starts individual MCP servers when aggregator unavailable
   - Lucidity MCP: `lucidity-mcp --transport sse --host 127.0.0.1 --port 6969`
   - Locust MCP: `locust-mcp --transport sse --host 127.0.0.1 --port 6970`

3. **Tertiary: Native Implementation Fallback**
   - Uses native Python implementations when MCP servers unavailable
   - Ensures tools remain functional in any environment

## Tools Provided

### Code Quality Analysis

**Tool**: `analyze_code_quality`

**MCP Server**: hyperb1iss/lucidity-mcp
- Static analysis using AST parsing
- Security vulnerability detection
- Code complexity analysis
- Style and formatting checks
- Performance issue identification

**Parameters**:
- `workspace_root`: Path to analyze
- `file_patterns`: Optional glob patterns for files to include
- `exclude_patterns`: Optional patterns to exclude
- `analysis_depth`: Level of analysis detail

**Output**:
```json
{
  "success": true,
  "connection_method": "aggregator|individual|native",
  "analysis": {
    "analysis_method": "mcp|native",
    "workspace_root": "/path/to/workspace",
    "total_files": 25,
    "total_lines": 1500,
    "issues": [
      {
        "dimension": "security",
        "severity": "high",
        "file": "example.py",
        "line": 42,
        "description": "Use of shell=True in subprocess call",
        "suggestion": "Use shell=False and pass command as list"
      }
    ],
    "metrics": {
      "code_complexity": 3.2,
      "maintainability_index": 85.5,
      "technical_debt_minutes": 45
    }
  }
}
```

### Load/Performance Testing

**Tool**: `run_load_test`

**MCP Server**: qainsights/locust-mcp-server
- HTTP load testing with Locust
- Performance metrics collection
- Custom test scenario support
- Real-time monitoring

**Parameters**:
- `test_file`: Path to Locust test script
- `target_host`: Target URL for testing
- `users`: Number of concurrent users
- `spawn_rate`: User spawn rate per second
- `runtime`: Test duration (e.g., "30s", "5m")
- `headless`: Run without web UI

**Output**:
```json
{
  "success": true,
  "connection_method": "aggregator|individual|native",
  "load_test_results": {
    "test_method": "mcp|native",
    "metrics": {
      "total_requests": 1250,
      "failed_requests": 2,
      "avg_response_time": 145.2,
      "min_response_time": 12.5,
      "max_response_time": 2500.0,
      "requests_per_second": 41.7,
      "failure_rate": 0.16
    },
    "duration": "30.1s",
    "target_host": "https://api.example.com"
  }
}
```

### Test Script Generation

**Tool**: `create_test_script`

**MCP Server**: qainsights/locust-mcp-server
- Generates Locust test scripts
- API endpoint discovery
- Load pattern templates

### Performance Profiling

**Tool**: `profile_performance`

**MCP Server**: hyperb1iss/lucidity-mcp
- Code performance profiling
- Memory usage analysis
- Execution bottleneck identification

## Configuration

### Environment Variables

```bash
# Aggregator Configuration
MCP_AGGREGATOR_URL=http://localhost:8080

# Individual Server Ports
LUCIDITY_MCP_PORT=6969
LOCUST_MCP_PORT=6970

# Optional: Disable specific connection methods
MCP_AGGREGATOR_ENABLED=true
MCP_INDIVIDUAL_SERVERS_ENABLED=true
MCP_NATIVE_FALLBACK_ENABLED=true
```

### MCP Configuration Object

```python
MCP_CONFIG = {
    "aggregator": {
        "enabled": True,
        "url": "http://localhost:8080",
        "timeout": 5,
        "lucidity_endpoint": "/lucidity",
        "locust_endpoint": "/locust"
    },
    "individual_servers": {
        "lucidity": {
            "port": 6969,
            "host": "127.0.0.1",
            "start_command": ["lucidity-mcp", "--transport", "sse"],
            "health_endpoint": "/sse"
        },
        "locust": {
            "port": 6970,
            "host": "127.0.0.1",
            "start_command": ["locust-mcp", "--transport", "sse"],
            "health_endpoint": "/health"
        }
    },
    "fallback_native": True,
    "startup_timeout": 30,
    "health_check_interval": 10
}
```

## Usage Examples

### Code Quality Analysis

```python
from dev_team.tools.mcp_qa_tools import analyze_code_quality

# Analyze entire workspace
result = analyze_code_quality.invoke({
    'workspace_root': '/path/to/project'
})

# Analyze specific file patterns
result = analyze_code_quality.invoke({
    'workspace_root': '/path/to/project',
    'file_patterns': ['*.py', '*.js'],
    'exclude_patterns': ['**/tests/**', '**/node_modules/**']
})
```

### Load Testing

```python
from dev_team.tools.mcp_qa_tools import run_load_test

# Basic load test
result = run_load_test.invoke({
    'test_file': 'load_tests/api_test.py',
    'target_host': 'https://api.example.com',
    'users': 50,
    'spawn_rate': 5,
    'runtime': '2m'
})
```

## Connection Manager

The `MCPConnectionManager` class orchestrates the hybrid connection strategy:

### Key Methods

- `check_aggregator_health()`: Validates aggregator availability
- `start_individual_server(server_name)`: Launches individual MCP servers
- `get_connection_info(service)`: Returns connection details for a service
- `_check_command_exists(command)`: Validates command availability

### Connection Flow

1. **Aggregator Check**: Attempts connection to configured aggregator
2. **Individual Server Startup**: If aggregator unavailable, starts individual servers
3. **Native Fallback**: Uses Python implementations if MCP unavailable
4. **Health Monitoring**: Continuous health checks for optimal routing

## Recommended Aggregators

Based on research, the following aggregators are recommended for production use:

1. **MCPX** (github.com/wong2/mcpx)
   - Lightweight proxy server
   - Docker support
   - Active development

2. **mcgravity** (github.com/cyanheads/mcgravity)
   - Production-ready aggregator
   - Multiple server support
   - Comprehensive logging

3. **pluggedin-mcp-proxy** (github.com/LLMplugging/pluggedin-mcp-proxy)
   - Enterprise features
   - Load balancing
   - Authentication support

## Installation Requirements

### For MCP Server Support

```bash
# Lucidity MCP Server
pip install lucidity-mcp

# Locust MCP Server  
pip install locust-mcp-server

# Optional: Install aggregator
docker pull mcpx/server:latest
# or
docker pull mcgravity/server:latest
```

### For Native Fallback Only

```bash
pip install ast  # Built-in
pip install locust
pip install requests
```

## Error Handling

The implementation includes comprehensive error handling:

- **Connection Failures**: Graceful fallback between connection methods
- **Command Not Found**: Clear error messages when MCP servers unavailable
- **Timeout Handling**: Configurable timeouts for all operations
- **Resource Cleanup**: Proper cleanup of server processes and temporary files

## Monitoring and Logging

- **Connection Method Tracking**: Each response indicates which connection method was used
- **Performance Metrics**: Timing and success rate tracking for each method
- **Health Check Logging**: Regular health status updates
- **Error Aggregation**: Centralized error logging with context

## Future Enhancements

1. **Additional MCP Servers**: Integration with more specialized QA tools
2. **Custom Aggregator**: Purpose-built aggregator for QA workflows
3. **Distributed Testing**: Multi-node load testing coordination
4. **CI/CD Integration**: Pipeline-specific QA automation
5. **Reporting Dashboard**: Real-time QA metrics visualization

## Security Considerations

- **Command Injection Prevention**: Safe subprocess execution
- **Network Security**: Configurable timeouts and validation
- **Access Control**: Support for authentication in aggregator mode
- **Data Privacy**: No sensitive data transmitted to external services

This implementation provides a robust, scalable foundation for QA and testing capabilities while maintaining flexibility and reliability across different deployment scenarios.
