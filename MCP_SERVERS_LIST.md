# MCP Servers Used in LIMCO Application

This is a comprehensive list of all MCP servers used in the LIMCO application that you can configure in your self-hosted aggregator.

## 📋 Complete MCP Servers List

### 1. **QA & Testing Tools** (`mcp_qa_tools.py`)

| Server Name | Command | Default Port | Repository/Package | Purpose |
|-------------|---------|--------------|-------------------|----------|
| **lucidity-mcp** | `lucidity-mcp --transport sse` | 6969 | hyperb1iss/lucidity-mcp | Code quality analysis, security scanning, complexity metrics |
| **locust-mcp** | `locust-mcp --transport sse` | 6970 | qainsights/locust-mcp-server | Load testing, performance testing, HTTP benchmarking |

**Aggregator Endpoints:**
- `/lucidity` - Code quality analysis
- `/locust` - Load testing

**Environment Variables:**
- `LUCIDITY_MCP_PORT=6969`
- `LOCUST_MCP_PORT=6970`

---

### 2. **File Operations** (`mcp_file_operations.py`)

| Server Name | Command | Default Port | Repository/Package | Purpose |
|-------------|---------|--------------|-------------------|----------|
| **filescopemcp** | `filescopemcp --transport sse` | 6971 | File system operations | File analysis, project structure, file importance ranking |
| **mcp-text-editor** | `mcp-text-editor --transport sse` | 6972 | Text editing MCP | File editing, text manipulation, content operations |
| **mcp-language-server** | `mcp-language-server --transport sse` | 6973 | Language server MCP | Language-specific file operations, syntax analysis |

**Aggregator Endpoints:**
- `/filescopemcp` - File system operations
- `/texteditor` - Text editing operations  
- `/languageserver` - Language server operations

**Environment Variables:**
- `FILESCOPEMCP_PORT=6971`
- `TEXTEDITOR_MCP_PORT=6972`
- `LANGUAGESERVER_MCP_PORT=6973`

---

### 3. **Code Execution** (`mcp_code_execution.py`)

| Server Name | Command | Default Port | Repository/Package | Purpose |
|-------------|---------|--------------|-------------------|----------|
| **mcp-run-python** | `mcp-run-python --transport sse` | 6974 | Python execution MCP | Secure Python code execution, package installation |
| **deno-mcp-executor** | `deno-mcp-executor --transport sse` | 6975 | Deno execution MCP | TypeScript/JavaScript execution, Deno runtime |

**Aggregator Endpoints:**
- `/python-executor` - Python code execution
- `/deno-executor` - Deno/TypeScript execution

**Environment Variables:**
- `PYTHON_EXECUTOR_MCP_PORT=6974`
- `DENO_EXECUTOR_MCP_PORT=6975`

---

### 4. **Code Analysis** (`mcp_code_analysis.py`)

| Server Name | Command | Default Port | Repository/Package | Purpose |
|-------------|---------|--------------|-------------------|----------|
| **serena** | `uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context ide-assistant` | 6976 | oraios/serena | Advanced code analysis, repository understanding, IDE assistance |
| **repo-mapper-mcp** | `repo-mapper-mcp --transport sse` | 6977 | Repository mapping MCP | Repository structure analysis, code mapping, dependency analysis |

**Aggregator Endpoints:**
- `/serena` - Advanced code analysis
- `/repo-mapper` - Repository structure analysis

**Environment Variables:**
- `SERENA_MCP_PORT=6976`
- `REPO_MAPPER_MCP_PORT=6977`

---

### 5. **GitHub Integration** (`github_mcp.py`)

| Server Name | Command | Default Port | Repository/Package | Purpose |
|-------------|---------|--------------|-------------------|----------|
| **github-mcp-server** | `github-mcp-server` | 6978 | Local GitHub MCP server | GitHub API operations, repository management, user info |

**Aggregator Endpoints:**
- `/github` - GitHub API operations

**Environment Variables:**
- `GITHUB_MCP_SERVER_PORT=6978`

---

## 🔧 Aggregator Configuration

### Required Aggregator Endpoints

Your self-hosted MCP aggregator should expose these endpoints:

```yaml
endpoints:
  # QA & Testing
  /lucidity: 
    target: "http://localhost:6969"
    transport: "sse"
  /locust:
    target: "http://localhost:6970" 
    transport: "sse"
    
  # File Operations
  /filescopemcp:
    target: "http://localhost:6971"
    transport: "sse"
  /texteditor:
    target: "http://localhost:6972"
    transport: "sse"
  /languageserver:
    target: "http://localhost:6973"
    transport: "sse"
    
  # Code Execution
  /python-executor:
    target: "http://localhost:6974"
    transport: "sse"
  /deno-executor:
    target: "http://localhost:6975"
    transport: "sse"
    
  # Code Analysis  
  /serena:
    target: "http://localhost:6976"
    transport: "sse"
  /repo-mapper:
    target: "http://localhost:6977"
    transport: "sse"
    
  # GitHub Integration
  /github:
    target: "http://localhost:6978"
    transport: "stdio"  # Note: GitHub MCP uses stdio transport
```

### Application Configuration

Set this environment variable to point to your aggregator:

```bash
export MCP_AGGREGATOR_URL="http://your-aggregator-host:8080"
```

## 📦 Installation Commands

Here are the installation commands for each MCP server:

```bash
# QA & Testing
pip install lucidity-mcp
pip install locust-mcp-server

# File Operations
pip install filescopemcp
pip install mcp-text-editor
pip install mcp-language-server

# Code Execution
pip install mcp-run-python
pip install deno-mcp-executor

# Code Analysis
# Serena is installed via uvx (see command above)
pip install repo-mapper-mcp

# GitHub (local server in this repo)
# Available at: ./github-mcp-server/
```

## 🚀 Benefits of Using Aggregator

1. **Single Connection Point**: Application connects to one aggregator instead of 10+ individual servers
2. **Load Balancing**: Distribute requests across multiple server instances
3. **Service Discovery**: Automatic routing to healthy server instances
4. **Centralized Monitoring**: Monitor all MCP services from one place
5. **Configuration Management**: Single point for server configuration
6. **Fault Tolerance**: Aggregator can handle individual server failures

## 🔄 Fallback Strategy

The application implements a 3-tier hybrid strategy:

1. **Primary**: MCP Aggregator (your self-hosted instance)
2. **Secondary**: Individual MCP servers (direct connection)
3. **Tertiary**: Native implementations (always available)

This ensures 100% uptime even if some MCP servers are unavailable.

---

**Total MCP Servers: 10**
- QA & Testing: 2 servers
- File Operations: 3 servers  
- Code Execution: 2 servers
- Code Analysis: 2 servers
- GitHub Integration: 1 server

All servers use SSE transport except the GitHub MCP server which uses stdio transport.
