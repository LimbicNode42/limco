"""Comprehensive tool collection for all development team agents.

All agents have access to all tools, with role-appropriate usage guided by prompting.
Tools are organized by category for clarity but shared across all agent types.
Enhanced with Command() and Send() capabilities for agent handoffs and collaboration.
"""

from typing import Dict, List, Any, Optional, Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.types import Command
from langgraph.prebuilt import InjectedState
import requests
import os
import json
import subprocess
import states
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_tavily import TavilySearch
# GitHub MCP Integration
try:
    from .github_mcp import GitHubMCPClient, create_github_mcp_tools, get_github_token
except ImportError:
    try:
        from github_mcp import GitHubMCPClient, create_github_mcp_tools, get_github_token
    except ImportError:
        print("Warning: GitHub MCP integration not available - github_mcp module not found")
        GitHubMCPClient = None
        create_github_mcp_tools = None
        get_github_token = None


def safe_get_state_attr(state: states.State, key: str, default=None):
    """Safely get state attribute whether state is dict-like or object-like."""
    if hasattr(state, 'get'):
        return safe_get_state_attr(state, key, default)
    return getattr(state, key, default)
from datetime import datetime


# =============================================================================
# AGENT HANDOFF AND COLLABORATION TOOLS (NEW!)
# =============================================================================

@tool
def transfer_to_qa_engineer(
    reason: Annotated[str, "Reason for transferring to QA"],
    context: Annotated[str, "Context and details for QA engineer"],
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    priority: str = "medium"
) -> Command:
    """Transfer work to QA engineer for testing and quality assurance."""
    tool_message = {
        "role": "tool",
        "content": f"Work transferred to QA engineer. Reason: {reason}",
        "name": "transfer_to_qa_engineer",
        "tool_call_id": tool_call_id,
    }
    
    return Command(
        goto="qa_engineer",
        update={
            "messages": safe_get_state_attr(state, "messages", []) + [tool_message],
            "handoff_reason": reason,
            "handoff_context": context,
            "priority": priority,
            "current_agent": "qa_engineer"
        },
        graph=Command.PARENT,
    )


@tool
def escalate_to_cto(
    issue: Annotated[str, "Issue requiring CTO attention"],
    urgency: Annotated[str, "Urgency level: low, medium, high, critical"],
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """Escalate complex technical or strategic decisions to CTO."""
    tool_message = {
        "role": "tool",
        "content": f"Issue escalated to CTO: {issue}",
        "name": "escalate_to_cto", 
        "tool_call_id": tool_call_id,
    }
    
    return Command(
        goto="cto",
        update={
            "messages": safe_get_state_attr(state, "messages", []) + [tool_message],
            "escalation_issue": issue,
            "escalation_urgency": urgency,
            "requires_cto_decision": True,
            "current_agent": "cto"
        },
        graph=Command.PARENT,
    )


@tool
def request_peer_review(
    work_description: Annotated[str, "Description of work needing review"],
    review_focus: Annotated[str, "Specific areas to focus review on"],
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """Request peer review of completed work."""
    tool_message = {
        "role": "tool",
        "content": f"Peer review requested for: {work_description}",
        "name": "request_peer_review",
        "tool_call_id": tool_call_id,
    }
    
    return Command(
        goto="peer_review_evaluator",
        update={
            "messages": safe_get_state_attr(state, "messages", []) + [tool_message],
            "review_work": work_description,
            "review_focus": review_focus,
            "review_type": "peer_review",
            "current_agent": "peer_review_evaluator"
        },
        graph=Command.PARENT,
    )


@tool
def delegate_to_engineering_manager(
    task_breakdown: Annotated[str, "Description of tasks to delegate"],
    coordination_needed: Annotated[bool, "Whether coordination between engineers is needed"],
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """Delegate complex work requiring team coordination to engineering manager."""
    tool_message = {
        "role": "tool",
        "content": f"Work delegated to engineering manager: {task_breakdown}",
        "name": "delegate_to_engineering_manager",
        "tool_call_id": tool_call_id,
    }
    
    return Command(
        goto="engineering_manager",
        update={
            "messages": safe_get_state_attr(state, "messages", []) + [tool_message],
            "delegated_tasks": task_breakdown,
            "requires_coordination": coordination_needed,
            "current_agent": "engineering_manager"
        },
        graph=Command.PARENT,
    )


@tool
def transfer_to_senior_engineer(
    task_description: Annotated[str, "Description of development task"],
    technical_requirements: Annotated[str, "Specific technical requirements"],
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """Transfer development work to senior engineer."""
    tool_message = {
        "role": "tool",
        "content": f"Development task assigned to senior engineer: {task_description}",
        "name": "transfer_to_senior_engineer",
        "tool_call_id": tool_call_id,
    }
    
    return Command(
        goto="senior_engineer",
        update={
            "messages": safe_get_state_attr(state, "messages", []) + [tool_message],
            "assigned_task": task_description,
            "technical_requirements": technical_requirements,
            "current_agent": "senior_engineer"
        },
        graph=Command.PARENT,
    )


@tool
def escalate_to_human(
    decision_needed: Annotated[str, "Decision requiring human judgment"],
    background_context: Annotated[str, "Background context for the human"],
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """Escalate decisions requiring human judgment to human evaluator."""
    tool_message = {
        "role": "tool",
        "content": f"Escalated to human: {decision_needed}",
        "name": "escalate_to_human",
        "tool_call_id": tool_call_id,
    }
    
    return Command(
        goto="human_escalation_evaluator",
        update={
            "messages": safe_get_state_attr(state, "messages", []) + [tool_message],
            "human_decision_needed": decision_needed,
            "decision_context": background_context,
            "requires_human_input": True,
            "current_agent": "human_escalation_evaluator"
        },
        graph=Command.PARENT,
    )


# =============================================================================
# RESEARCH & COMMUNICATION TOOLS  
# =============================================================================

@tool
def web_search(query: str, num_results: int = 5, search_type: str = "general") -> str:
    """Search the web for information using multiple search engines.
    
    This tool provides comprehensive web search using both Serper (Google) and Tavily APIs.
    It automatically tries Tavily first (faster, AI-optimized) and falls back to Serper if needed.
    
    Args:
        query: The search query string
        num_results: Number of results to return (default 5, max 10)
        search_type: Type of search - "general", "news", "academic", or "recent"
        
    Returns:
        Formatted search results with titles, URLs, and snippets
    """
    try:
        # Limit results to avoid overwhelming context
        num_results = min(num_results, 10)
        
        # Try Tavily first (optimized for AI agents)
        tavily_results = _search_with_tavily(query, num_results, search_type)
        if tavily_results:
            return tavily_results
            
        # Fallback to Serper (Google Search)
        serper_results = _search_with_serper(query, num_results, search_type)
        if serper_results:
            return serper_results
            
        return f"No search results found for '{query}'. Please check your internet connection or try a different query."
        
    except Exception as e:
        return f"Search error for '{query}': {str(e)}"


def _search_with_tavily(query: str, num_results: int, search_type: str) -> Optional[str]:
    """Search using Tavily API - optimized for AI agents."""
    try:
        # Configure Tavily based on search type
        tavily_config = {
            "max_results": num_results,
            "include_answer": True,
            "include_raw_content": False,
            "include_images": False,
        }
        
        if search_type == "news":
            tavily_config["topic"] = "news"
        elif search_type == "recent":
            tavily_config["search_depth"] = "advanced"
            tavily_config["time_range"] = "week"
        elif search_type == "academic":
            tavily_config["search_depth"] = "advanced"
            tavily_config["include_domains"] = ["scholar.google.com", "arxiv.org", "pubmed.ncbi.nlm.nih.gov"]
        else:
            tavily_config["topic"] = "general"
            
        search_tool = TavilySearch(**tavily_config)
        
        # Execute search
        results = search_tool.invoke({"query": query})
        
        if not results:
            return None
            
        # Parse and format results
        return _format_tavily_results(query, results, search_type)
        
    except Exception as e:
        print(f"Tavily search failed: {e}")
        return None


def _search_with_serper(query: str, num_results: int, search_type: str) -> Optional[str]:
    """Search using Google Serper API."""
    try:
        # Configure Serper based on search type  
        serper_config = {"k": num_results}
        
        if search_type == "news":
            serper_config["type"] = "news"
        elif search_type == "recent":
            serper_config["tbs"] = "qdr:w"  # Past week
        elif search_type == "academic":
            serper_config["type"] = "search"
            # Add academic-focused terms to query
            query = f"{query} site:scholar.google.com OR site:arxiv.org OR site:pubmed.ncbi.nlm.nih.gov"
        else:
            serper_config["type"] = "search"
            
        search_wrapper = GoogleSerperAPIWrapper(**serper_config)
        
        # Execute search
        if search_type == "news" or search_type in ["general", "recent", "academic"]:
            results = search_wrapper.results(query)
        else:
            results = search_wrapper.run(query)
            
        if not results:
            return None
            
        # Format results based on type
        return _format_serper_results(query, results, search_type)
        
    except Exception as e:
        print(f"Serper search failed: {e}")
        return None


def _format_tavily_results(query: str, results: str, search_type: str) -> str:
    """Format Tavily search results."""
    try:
        # Parse JSON response if it's a string
        if isinstance(results, str):
            data = json.loads(results)
        else:
            data = results
            
        formatted_results = [f"🔍 Web Search Results for '{query}' (via Tavily)\n"]
        formatted_results.append(f"Search Type: {search_type.title()}\n")
        
        # Add answer if available
        if data.get("answer"):
            formatted_results.append(f"📋 **Quick Answer**: {data['answer']}\n")
            
        # Add search results
        if data.get("results"):
            formatted_results.append("📄 **Detailed Results**:")
            for i, result in enumerate(data["results"][:10], 1):
                title = result.get("title", "No title")
                url = result.get("url", "No URL")
                content = result.get("content", "No content available")
                
                # Truncate content to avoid overwhelming context
                if len(content) > 200:
                    content = content[:200] + "..."
                    
                formatted_results.append(f"\n{i}. **{title}**")
                formatted_results.append(f"   🔗 {url}")
                formatted_results.append(f"   📝 {content}")
                
        return "\n".join(formatted_results)
        
    except Exception as e:
        return f"Error formatting Tavily results: {str(e)}"


def _format_serper_results(query: str, results: Any, search_type: str) -> str:
    """Format Google Serper search results."""
    try:
        formatted_results = [f"🔍 Web Search Results for '{query}' (via Google/Serper)\n"]
        formatted_results.append(f"Search Type: {search_type.title()}\n")
        
        if isinstance(results, str):
            # Simple string result
            return f"🔍 Web Search Results for '{query}':\n{results}"
            
        elif isinstance(results, dict):
            # Structured results
            if search_type == "news" and "news" in results:
                formatted_results.append("📰 **News Results**:")
                for i, item in enumerate(results["news"][:10], 1):
                    title = item.get("title", "No title")
                    link = item.get("link", "No URL")
                    snippet = item.get("snippet", "No description")
                    source = item.get("source", "Unknown source")
                    date = item.get("date", "")
                    
                    formatted_results.append(f"\n{i}. **{title}**")
                    formatted_results.append(f"   📅 {date} | 📺 {source}")
                    formatted_results.append(f"   🔗 {link}")
                    formatted_results.append(f"   📝 {snippet}")
                    
            elif "organic" in results:
                # Regular search results
                formatted_results.append("📄 **Search Results**:")
                for i, item in enumerate(results["organic"][:10], 1):
                    title = item.get("title", "No title")
                    link = item.get("link", "No URL")
                    snippet = item.get("snippet", "No description")
                    
                    formatted_results.append(f"\n{i}. **{title}**")
                    formatted_results.append(f"   🔗 {link}")
                    formatted_results.append(f"   📝 {snippet}")
                    
            # Add knowledge graph if available
            if "knowledgeGraph" in results:
                kg = results["knowledgeGraph"]
                formatted_results.append(f"\n🧠 **Knowledge Graph**: {kg.get('title', '')}")
                if kg.get("description"):
                    formatted_results.append(f"   📝 {kg['description']}")
                    
        return "\n".join(formatted_results)
        
    except Exception as e:
        return f"Error formatting Serper results: {str(e)}"


@tool  
def web_search_news(query: str, num_results: int = 5, time_range: str = "week") -> str:
    """Search for recent news articles about a topic.
    
    Args:
        query: News search query
        num_results: Number of results (default 5, max 10)
        time_range: "day", "week", "month", or "year"
        
    Returns:
        Formatted news search results
    """
    try:
        # Limit results to avoid overwhelming context
        num_results = min(num_results, 10)
        
        # Try Tavily first for news
        tavily_results = _search_with_tavily(query, num_results, "news")
        if tavily_results:
            return tavily_results
            
        # Fallback to Serper for news
        serper_results = _search_with_serper(query, num_results, "news")
        if serper_results:
            return serper_results
            
        return f"No news results found for '{query}'. Please try a different query."
        
    except Exception as e:
        return f"News search error for '{query}': {str(e)}"


@tool
def web_search_academic(query: str, num_results: int = 5) -> str:
    """Search for academic papers and scholarly articles.
    
    Args:
        query: Academic search query
        num_results: Number of results (default 5, max 10)
        
    Returns:
        Formatted academic search results
    """
    try:
        # Limit results to avoid overwhelming context
        num_results = min(num_results, 10)
        
        # Try Tavily first for academic content
        tavily_results = _search_with_tavily(query, num_results, "academic")
        if tavily_results:
            return tavily_results
            
        # Fallback to Serper for academic content
        serper_results = _search_with_serper(query, num_results, "academic")
        if serper_results:
            return serper_results
            
        return f"No academic results found for '{query}'. Please try a different query."
        
    except Exception as e:
        return f"Academic search error for '{query}': {str(e)}"


@tool
def send_message(recipient: str, message: str, priority: str = "normal") -> str:
    """Send a message to another team member or stakeholder.
    
    Args:
        recipient: The person or team to send the message to
        message: The message content
        priority: Message priority (low, normal, high, urgent)
        
    Returns:
        Confirmation of message sent
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"Message sent to {recipient} at {timestamp} (Priority: {priority}): {message[:50]}..."


@tool
def check_messages() -> str:
    """Check for new messages and notifications.
    
    Returns:
        List of recent messages and notifications
    """
    # Placeholder - would integrate with actual messaging system
    return "Recent messages:\n- CTO: Status update on API development\n- QA Team: Test results available\n..."


# =============================================================================
# DOCUMENT & KNOWLEDGE MANAGEMENT
# =============================================================================

@tool
def search_documents(query: str, doc_type: str = "all") -> str:
    """Search through project documentation and knowledge base.
    
    Args:
        query: Search terms for finding relevant documents
        doc_type: Type of documents (requirements, design, api, test, all)
        
    Returns:
        List of relevant documents with excerpts
    """
    return f"Document search for '{query}' in {doc_type} documents:\n- API Documentation: Section 3.2\n- Requirements Doc: User Story #45\n..."


@tool
def create_document(title: str, content: str, doc_type: str = "general") -> str:
    """Create a new document in the project knowledge base.
    
    Args:
        title: Document title
        content: Document content
        doc_type: Document type (requirements, design, api, test, meeting_notes)
        
    Returns:
        Confirmation with document ID
    """
    doc_id = f"DOC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    return f"Document created: {title} (ID: {doc_id}, Type: {doc_type})"


@tool
def update_document(doc_id: str, content: str) -> str:
    """Update an existing document.
    
    Args:
        doc_id: The document identifier to update
        content: New or additional content
        
    Returns:
        Confirmation of update
    """
    return f"Document {doc_id} updated successfully with new content"


# =============================================================================
# DATABASE & DATA TOOLS
# =============================================================================

@tool
def query_database(query: str, database: str = "main") -> str:
    """Execute a database query for project data.
    
    Args:
        query: SQL query to execute
        database: Target database (main, test, analytics)
        
    Returns:
        Query results in formatted text
    """
    # Placeholder - would execute actual database queries
    return f"Database query executed on {database}:\nResults: [Sample data rows...]"


@tool
def get_project_metrics() -> str:
    """Retrieve current project metrics and KPIs.
    
    Returns:
        Current project health metrics
    """
    return """Project Metrics:
- Tasks Completed: 45/60 (75%)
- Code Coverage: 82%
- Build Success Rate: 95%
- Bug Count: 12 open, 45 resolved
- Sprint Progress: Day 8/14"""


# =============================================================================
# FILESYSTEM & CODE TOOLS
# =============================================================================

@tool
def read_file(file_path: str) -> str:
    """Read the contents of a file.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        File contents as string
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"File contents of {file_path}:\n{content}"
    except Exception as e:
        return f"Error reading file {file_path}: {str(e)}"


@tool
def write_file(file_path: str, content: str) -> str:
    """Write content to a file.
    
    Args:
        file_path: Path where to write the file
        content: Content to write
        
    Returns:
        Confirmation of file written
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"File written successfully: {file_path}"
    except Exception as e:
        return f"Error writing file {file_path}: {str(e)}"


@tool
def list_files(directory: str = ".", pattern: str = "*") -> str:
    """List files in a directory with optional pattern matching.
    
    Args:
        directory: Directory to list files from
        pattern: File pattern to match (e.g., "*.py")
        
    Returns:
        List of matching files
    """
    try:
        import glob
        files = glob.glob(os.path.join(directory, pattern))
        return f"Files in {directory} matching '{pattern}':\n" + "\n".join(files)
    except Exception as e:
        return f"Error listing files: {str(e)}"


# =============================================================================
# CODE DEVELOPMENT TOOLS
# =============================================================================

@tool
def run_code(code: str, language: str = "python") -> str:
    """Execute code in a safe environment.
    
    Args:
        code: Code to execute
        language: Programming language (python, javascript, bash)
        
    Returns:
        Code execution results
    """
    # Placeholder - would execute in sandboxed environment
    return f"Code execution ({language}):\n{code}\n\nOutput: [Execution results would appear here]"


@tool
def run_tests(test_path: str = "tests/", test_type: str = "unit") -> str:
    """Run automated tests.
    
    Args:
        test_path: Path to test files
        test_type: Type of tests (unit, integration, e2e)
        
    Returns:
        Test execution results
    """
    return f"Running {test_type} tests from {test_path}:\n✅ 15 passed\n❌ 2 failed\n⚠️ 1 skipped"



# =============================================================================
# PROJECT MANAGEMENT TOOLS
# =============================================================================

@tool
def create_task(title: str, description: str, assignee: str = None, priority: str = "medium") -> str:
    """Create a new project task.
    
    Args:
        title: Task title
        description: Detailed task description
        assignee: Person assigned to the task
        priority: Task priority (low, medium, high, critical)
        
    Returns:
        Task creation confirmation with ID
    """
    task_id = f"TASK-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    return f"Task created: {title} (ID: {task_id}, Assignee: {assignee}, Priority: {priority})"


@tool
def update_task_status(task_id: str, status: str, notes: str = "") -> str:
    """Update the status of an existing task.
    
    Args:
        task_id: The task identifier
        status: New status (todo, in_progress, review, done, blocked)
        notes: Optional notes about the status change
        
    Returns:
        Status update confirmation
    """
    return f"Task {task_id} status updated to '{status}'. Notes: {notes}"


@tool
def get_team_workload() -> str:
    """Get current workload distribution across team members.
    
    Returns:
        Team workload summary
    """
    return """Team Workload:
- Alice (Senior Engineer): 8 tasks (3 in progress)
- Bob (QA Engineer): 5 tasks (2 in progress)
- Carol (Engineering Manager): 12 tasks (5 in progress)
- Dave (Senior Engineer): 6 tasks (2 in progress)"""


# =============================================================================
# EMAIL & COMMUNICATION TOOLS (Leadership)
# =============================================================================

@tool
def send_email(to: str, subject: str, body: str, cc: str = None) -> str:
    """Send an email to stakeholders.
    
    Args:
        to: Primary recipient email
        subject: Email subject line
        body: Email body content
        cc: CC recipients (optional)
        
    Returns:
        Email sent confirmation
    """
    return f"Email sent to {to} (CC: {cc}) - Subject: {subject}"


@tool
def schedule_meeting(title: str, participants: List[str], duration_minutes: int = 60, date_time: str = None) -> str:
    """Schedule a meeting with team members.
    
    Args:
        title: Meeting title
        participants: List of participant emails/names
        duration_minutes: Meeting duration in minutes
        date_time: Preferred date/time (if None, suggests next available)
        
    Returns:
        Meeting scheduling confirmation
    """
    meeting_id = f"MEET-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    return f"Meeting scheduled: {title} (ID: {meeting_id}, Participants: {len(participants)}, Duration: {duration_minutes}min)"


# =============================================================================
# TOOL COLLECTIONS FOR AGENT INITIALIZATION
# =============================================================================

async def get_github_mcp_tools():
    """Get GitHub MCP tools asynchronously."""
    if not create_github_mcp_tools or not get_github_token:
        print("Warning: GitHub MCP integration not available")
        return []
    
    try:
        token = get_github_token()
        # Focus on repository and issue management toolsets
        toolsets = ["repos", "issues", "pull_requests", "context"]
        tools = await create_github_mcp_tools(token, toolsets=toolsets)
        return tools
    except Exception as e:
        print(f"Warning: Failed to load GitHub MCP tools: {e}")
        return []


def get_github_mcp_tools_sync():
    """Get GitHub MCP tools synchronously (for use in get_all_tools)."""
    if not create_github_mcp_tools or not get_github_token:
        return []
        
    import asyncio
    try:
        # Check if we're in an async context
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, use run_coroutine_threadsafe
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, get_github_mcp_tools())
                return future.result(timeout=10)
        except RuntimeError:
            # No running loop, we can use asyncio.run
            return asyncio.run(get_github_mcp_tools())
    except Exception as e:
        print(f"Warning: Failed to load GitHub MCP tools synchronously: {e}")
        return []


def get_all_tools() -> List:
    """Get all available tools for agent initialization.
    
    Returns:
        List of all tool functions including handoff capabilities
    """
    base_tools = [
        # Agent Handoff & Collaboration (NEW!)
        transfer_to_qa_engineer, escalate_to_cto, request_peer_review,
        delegate_to_engineering_manager, transfer_to_senior_engineer, escalate_to_human,
        
        # Research & Communication
        web_search, web_search_news, web_search_academic, send_message, check_messages,
        
        # Document & Knowledge Management
        search_documents, create_document, update_document,
        
        # Database & Data
        query_database, get_project_metrics,
        
        # Filesystem & Code
        read_file, write_file, list_files,
        
        # Code Development
        run_code, run_tests,
        
        # Project Management
        create_task, update_task_status, get_team_workload,
        
        # Email & Communication (Leadership)
        send_email, schedule_meeting
    ]
    
    # Add GitHub MCP tools (enhanced GitHub integration with 45 tools)
    try:
        github_mcp_tools = get_github_mcp_tools_sync()
        if github_mcp_tools:
            base_tools.extend(github_mcp_tools)
            print(f"Enhanced GitHub integration: Added {len(github_mcp_tools)} MCP tools")
    except Exception as e:
        print(f"Warning: Could not load GitHub MCP tools: {e}")
    
    return base_tools


def get_tool_descriptions() -> Dict[str, str]:
    """Get descriptions of all available tools for agent awareness.
    
    Returns:
        Dictionary mapping tool names to their descriptions
    """
    tools = get_all_tools()
    return {tool.name: tool.description for tool in tools}
