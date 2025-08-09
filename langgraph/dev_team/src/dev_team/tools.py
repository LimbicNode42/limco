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
from langchain_community.agent_toolkits.github.toolkit import GitHubToolkit
from langchain_community.utilities.github import GitHubAPIWrapper


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
# GITHUB INTEGRATION TOOLS
# =============================================================================

def _get_github_toolkit(repository: str = None) -> GitHubToolkit:
    """Get GitHub toolkit instance with optional repository override.
    
    Args:
        repository: Repository name in format 'owner/repo'. If None, uses environment default.
        
    Returns:
        Configured GitHubToolkit instance
    """
    try:
        # Create GitHub API wrapper with optional repository override
        if repository:
            # Temporarily override the repository environment variable
            import os
            original_repo = os.environ.get("GITHUB_REPOSITORY")
            os.environ["GITHUB_REPOSITORY"] = repository
            try:
                github = GitHubAPIWrapper()
                toolkit = GitHubToolkit.from_github_api_wrapper(github, include_release_tools=True)
            finally:
                # Restore original repository setting
                if original_repo:
                    os.environ["GITHUB_REPOSITORY"] = original_repo
                else:
                    os.environ.pop("GITHUB_REPOSITORY", None)
        else:
            # Use default repository from environment
            github = GitHubAPIWrapper()
            toolkit = GitHubToolkit.from_github_api_wrapper(github, include_release_tools=True)
            
        return toolkit
    except Exception as e:
        print(f"Failed to initialize GitHub toolkit: {e}")
        return None


@tool
def github_get_issues(repository: str = None, state: str = "open", limit: int = 10) -> str:
    """Get issues from a GitHub repository.
    
    Args:
        repository: Repository name in format 'owner/repo' (default: from environment)
        state: Issue state - 'open', 'closed', or 'all' (default: 'open')
        limit: Maximum number of issues to return (default: 10)
        
    Returns:
        List of issues with details
    """
    try:
        toolkit = _get_github_toolkit(repository)
        if not toolkit:
            return "❌ Failed to initialize GitHub connection"
            
        # Get the issues tool
        tools = toolkit.get_tools()
        issues_tool = next((tool for tool in tools if tool.name == "Get Issues"), None)
        if not issues_tool:
            issues_tool = next((tool for tool in tools if "Get Issues" in tool.name), None)
        
        if not issues_tool:
            return "❌ Issues tool not found"
            
        # Execute the tool
        result = issues_tool.invoke({})
        
        return f"📋 **GitHub Issues** (Repository: {repository or 'default'})\n\n{result}"
        
    except Exception as e:
        return f"❌ Error fetching GitHub issues: {str(e)}"


@tool  
def github_get_issue(issue_number: int, repository: str = None) -> str:
    """Get details about a specific GitHub issue.
    
    Args:
        issue_number: The issue number to retrieve
        repository: Repository name in format 'owner/repo' (default: from environment)
        
    Returns:
        Detailed issue information
    """
    try:
        toolkit = _get_github_toolkit(repository)
        if not toolkit:
            return "❌ Failed to initialize GitHub connection"
            
        # Get the issue tool
        tools = toolkit.get_tools()
        issue_tool = next((tool for tool in tools if tool.name == "Get Issue"), None)
        if not issue_tool:
            issue_tool = next((tool for tool in tools if "Get Issue" in tool.name), None)
        
        if not issue_tool:
            return "❌ Issue tool not found"
            
        # Execute the tool
        result = issue_tool.invoke({"issue_number": issue_number})
        
        return f"🔍 **GitHub Issue #{issue_number}** (Repository: {repository or 'default'})\n\n{result}"
        
    except Exception as e:
        return f"❌ Error fetching GitHub issue #{issue_number}: {str(e)}"


@tool
def github_comment_on_issue(issue_number: int, comment: str, repository: str = None) -> str:
    """Add a comment to a GitHub issue.
    
    Args:
        issue_number: The issue number to comment on
        comment: The comment text to add
        repository: Repository name in format 'owner/repo' (default: from environment)
        
    Returns:
        Confirmation of comment posted
    """
    try:
        toolkit = _get_github_toolkit(repository)
        if not toolkit:
            return "❌ Failed to initialize GitHub connection"
            
        # Get the comment tool
        tools = toolkit.get_tools()
        comment_tool = next((tool for tool in tools if "Comment on Issue" in tool.name), None)
        
        if not comment_tool:
            return "❌ Comment tool not found"
            
        # Execute the tool
        result = comment_tool.invoke({
            "issue_number": issue_number,
            "comment": comment
        })
        
        return f"💬 **Comment Posted** on Issue #{issue_number} (Repository: {repository or 'default'})\n\n{result}"
        
    except Exception as e:
        return f"❌ Error commenting on GitHub issue #{issue_number}: {str(e)}"


@tool
def github_list_pull_requests(repository: str = None, state: str = "open") -> str:
    """List pull requests in a GitHub repository.
    
    Args:
        repository: Repository name in format 'owner/repo' (default: from environment)
        state: PR state - 'open', 'closed', or 'all' (default: 'open')
        
    Returns:
        List of pull requests with details
    """
    try:
        toolkit = _get_github_toolkit(repository)
        if not toolkit:
            return "❌ Failed to initialize GitHub connection"
            
        # Get the PR list tool
        tools = toolkit.get_tools()
        pr_tool = next((tool for tool in tools if "List open pull requests" in tool.name), None)
        
        if not pr_tool:
            return "❌ Pull requests tool not found"
            
        # Execute the tool
        result = pr_tool.invoke({})
        
        return f"🔄 **GitHub Pull Requests** (Repository: {repository or 'default'})\n\n{result}"
        
    except Exception as e:
        return f"❌ Error listing GitHub pull requests: {str(e)}"


@tool
def github_get_pull_request(pr_number: int, repository: str = None) -> str:
    """Get details about a specific GitHub pull request.
    
    Args:
        pr_number: The pull request number to retrieve
        repository: Repository name in format 'owner/repo' (default: from environment)
        
    Returns:
        Detailed pull request information
    """
    try:
        toolkit = _get_github_toolkit(repository)
        if not toolkit:
            return "❌ Failed to initialize GitHub connection"
            
        # Get the PR tool
        tools = toolkit.get_tools()
        pr_tool = next((tool for tool in tools if "Get Pull Request" in tool.name), None)
        
        if not pr_tool:
            return "❌ Pull request tool not found"
            
        # Execute the tool
        result = pr_tool.invoke({"pr_number": pr_number})
        
        return f"🔄 **GitHub Pull Request #{pr_number}** (Repository: {repository or 'default'})\n\n{result}"
        
    except Exception as e:
        return f"❌ Error fetching GitHub pull request #{pr_number}: {str(e)}"


@tool
def github_create_pull_request(title: str, body: str, head_branch: str = None, base_branch: str = None, repository: str = None) -> str:
    """Create a new GitHub pull request.
    
    Args:
        title: The title of the pull request
        body: The body/description of the pull request
        head_branch: The branch containing changes (default: from environment)
        base_branch: The target branch for merging (default: from environment)
        repository: Repository name in format 'owner/repo' (default: from environment)
        
    Returns:
        Details of the created pull request
    """
    try:
        toolkit = _get_github_toolkit(repository)
        if not toolkit:
            return "❌ Failed to initialize GitHub connection"
            
        # Get the create PR tool
        tools = toolkit.get_tools()
        create_pr_tool = next((tool for tool in tools if "Create Pull Request" in tool.name), None)
        
        if not create_pr_tool:
            return "❌ Create pull request tool not found"
            
        # Prepare PR data
        pr_data = {"title": title, "body": body}
        if head_branch:
            pr_data["head"] = head_branch
        if base_branch:
            pr_data["base"] = base_branch
            
        # Execute the tool
        result = create_pr_tool.invoke(pr_data)
        
        return f"✨ **GitHub Pull Request Created** (Repository: {repository or 'default'})\n\n{result}"
        
    except Exception as e:
        return f"❌ Error creating GitHub pull request: {str(e)}"


@tool
def github_create_file(file_path: str, content: str, commit_message: str, repository: str = None, branch: str = None) -> str:
    """Create a new file in a GitHub repository.
    
    Args:
        file_path: Path where the file should be created
        content: Content of the file
        commit_message: Commit message for the file creation
        repository: Repository name in format 'owner/repo' (default: from environment)
        branch: Branch to create the file on (default: from environment)
        
    Returns:
        Confirmation of file creation
    """
    try:
        toolkit = _get_github_toolkit(repository)
        if not toolkit:
            return "❌ Failed to initialize GitHub connection"
            
        # Get the create file tool
        tools = toolkit.get_tools()
        create_file_tool = next((tool for tool in tools if "Create File" in tool.name), None)
        
        if not create_file_tool:
            return "❌ Create file tool not found"
            
        # Execute the tool
        result = create_file_tool.invoke({
            "file_path": file_path,
            "file_contents": content,
            "commit_message": commit_message
        })
        
        return f"📄 **GitHub File Created** (Repository: {repository or 'default'})\nPath: {file_path}\n\n{result}"
        
    except Exception as e:
        return f"❌ Error creating GitHub file '{file_path}': {str(e)}"


@tool
def github_read_file(file_path: str, repository: str = None, branch: str = None) -> str:
    """Read a file from a GitHub repository.
    
    Args:
        file_path: Path to the file to read
        repository: Repository name in format 'owner/repo' (default: from environment)
        branch: Branch to read from (default: from environment)
        
    Returns:
        File contents
    """
    try:
        toolkit = _get_github_toolkit(repository)
        if not toolkit:
            return "❌ Failed to initialize GitHub connection"
            
        # Get the read file tool
        tools = toolkit.get_tools()
        read_file_tool = next((tool for tool in tools if "Read File" in tool.name), None)
        
        if not read_file_tool:
            return "❌ Read file tool not found"
            
        # Execute the tool
        result = read_file_tool.invoke({"file_path": file_path})
        
        return f"📖 **GitHub File Content** (Repository: {repository or 'default'})\nPath: {file_path}\n\n{result}"
        
    except Exception as e:
        return f"❌ Error reading GitHub file '{file_path}': {str(e)}"


@tool
def github_update_file(file_path: str, content: str, commit_message: str, repository: str = None, branch: str = None) -> str:
    """Update an existing file in a GitHub repository.
    
    Args:
        file_path: Path to the file to update
        content: New content for the file
        commit_message: Commit message for the update
        repository: Repository name in format 'owner/repo' (default: from environment)
        branch: Branch to update the file on (default: from environment)
        
    Returns:
        Confirmation of file update
    """
    try:
        toolkit = _get_github_toolkit(repository)
        if not toolkit:
            return "❌ Failed to initialize GitHub connection"
            
        # Get the update file tool
        tools = toolkit.get_tools()
        update_file_tool = next((tool for tool in tools if "Update File" in tool.name), None)
        
        if not update_file_tool:
            return "❌ Update file tool not found"
            
        # Execute the tool
        result = update_file_tool.invoke({
            "file_path": file_path,
            "file_contents": content,
            "commit_message": commit_message
        })
        
        return f"✏️ **GitHub File Updated** (Repository: {repository or 'default'})\nPath: {file_path}\n\n{result}"
        
    except Exception as e:
        return f"❌ Error updating GitHub file '{file_path}': {str(e)}"


@tool
def github_delete_file(file_path: str, commit_message: str, repository: str = None, branch: str = None) -> str:
    """Delete a file from a GitHub repository.
    
    Args:
        file_path: Path to the file to delete
        commit_message: Commit message for the deletion
        repository: Repository name in format 'owner/repo' (default: from environment)
        branch: Branch to delete the file from (default: from environment)
        
    Returns:
        Confirmation of file deletion
    """
    try:
        toolkit = _get_github_toolkit(repository)
        if not toolkit:
            return "❌ Failed to initialize GitHub connection"
            
        # Get the delete file tool
        tools = toolkit.get_tools()
        delete_file_tool = next((tool for tool in tools if "Delete File" in tool.name), None)
        
        if not delete_file_tool:
            return "❌ Delete file tool not found"
            
        # Execute the tool
        result = delete_file_tool.invoke({
            "file_path": file_path,
            "commit_message": commit_message
        })
        
        return f"🗑️ **GitHub File Deleted** (Repository: {repository or 'default'})\nPath: {file_path}\n\n{result}"
        
    except Exception as e:
        return f"❌ Error deleting GitHub file '{file_path}': {str(e)}"


@tool
def github_list_branches(repository: str = None) -> str:
    """List all branches in a GitHub repository.
    
    Args:
        repository: Repository name in format 'owner/repo' (default: from environment)
        
    Returns:
        List of repository branches
    """
    try:
        toolkit = _get_github_toolkit(repository)
        if not toolkit:
            return "❌ Failed to initialize GitHub connection"
            
        # Get the list branches tool
        tools = toolkit.get_tools()
        branches_tool = next((tool for tool in tools if "List branches" in tool.name), None)
        
        if not branches_tool:
            return "❌ List branches tool not found"
            
        # Execute the tool
        result = branches_tool.invoke({})
        
        return f"🌿 **GitHub Branches** (Repository: {repository or 'default'})\n\n{result}"
        
    except Exception as e:
        return f"❌ Error listing GitHub branches: {str(e)}"


@tool
def github_create_branch(branch_name: str, source_branch: str = None, repository: str = None) -> str:
    """Create a new branch in a GitHub repository.
    
    Args:
        branch_name: Name of the new branch to create
        source_branch: Branch to create from (default: repository default branch)
        repository: Repository name in format 'owner/repo' (default: from environment)
        
    Returns:
        Confirmation of branch creation
    """
    try:
        toolkit = _get_github_toolkit(repository)
        if not toolkit:
            return "❌ Failed to initialize GitHub connection"
            
        # Get the create branch tool
        tools = toolkit.get_tools()
        create_branch_tool = next((tool for tool in tools if "Create a new branch" in tool.name), None)
        
        if not create_branch_tool:
            return "❌ Create branch tool not found"
            
        # Execute the tool
        result = create_branch_tool.invoke({"branch_name": branch_name})
        
        return f"🌱 **GitHub Branch Created** (Repository: {repository or 'default'})\nBranch: {branch_name}\n\n{result}"
        
    except Exception as e:
        return f"❌ Error creating GitHub branch '{branch_name}': {str(e)}"


@tool
def github_set_active_branch(branch_name: str, repository: str = None) -> str:
    """Set the active branch for GitHub operations.
    
    Args:
        branch_name: Name of the branch to set as active
        repository: Repository name in format 'owner/repo' (default: from environment)
        
    Returns:
        Confirmation of active branch change
    """
    try:
        toolkit = _get_github_toolkit(repository)
        if not toolkit:
            return "❌ Failed to initialize GitHub connection"
            
        # Get the set active branch tool
        tools = toolkit.get_tools()
        set_branch_tool = next((tool for tool in tools if "Set active branch" in tool.name), None)
        
        if not set_branch_tool:
            return "❌ Set active branch tool not found"
            
        # Execute the tool
        result = set_branch_tool.invoke({"branch_name": branch_name})
        
        return f"🎯 **GitHub Active Branch Set** (Repository: {repository or 'default'})\nActive Branch: {branch_name}\n\n{result}"
        
    except Exception as e:
        return f"❌ Error setting GitHub active branch '{branch_name}': {str(e)}"


@tool
def github_search_code(query: str, repository: str = None, language: str = None) -> str:
    """Search for code in a GitHub repository.
    
    Args:
        query: Search query for code
        repository: Repository name in format 'owner/repo' (default: from environment)
        language: Programming language filter (optional)
        
    Returns:
        Code search results
    """
    try:
        toolkit = _get_github_toolkit(repository)
        if not toolkit:
            return "❌ Failed to initialize GitHub connection"
            
        # Get the search code tool
        tools = toolkit.get_tools()
        search_tool = next((tool for tool in tools if "Search code" in tool.name), None)
        
        if not search_tool:
            return "❌ Search code tool not found"
            
        # Build search query
        search_query = query
        if language:
            search_query = f"{query} language:{language}"
            
        # Execute the tool
        result = search_tool.invoke({"query": search_query})
        
        return f"🔍 **GitHub Code Search** (Repository: {repository or 'default'})\nQuery: {query}\n\n{result}"
        
    except Exception as e:
        return f"❌ Error searching GitHub code: {str(e)}"


@tool
def github_search_issues(query: str, repository: str = None, state: str = None) -> str:
    """Search for issues and pull requests in a GitHub repository.
    
    Args:
        query: Search query for issues and PRs
        repository: Repository name in format 'owner/repo' (default: from environment)
        state: Issue state filter - 'open', 'closed' (optional)
        
    Returns:
        Issues and PR search results
    """
    try:
        toolkit = _get_github_toolkit(repository)
        if not toolkit:
            return "❌ Failed to initialize GitHub connection"
            
        # Get the search issues tool
        tools = toolkit.get_tools()
        search_tool = next((tool for tool in tools if "Search issues" in tool.name), None)
        
        if not search_tool:
            return "❌ Search issues tool not found"
            
        # Build search query
        search_query = query
        if state:
            search_query = f"{query} state:{state}"
            
        # Execute the tool
        result = search_tool.invoke({"query": search_query})
        
        return f"🔍 **GitHub Issues Search** (Repository: {repository or 'default'})\nQuery: {query}\n\n{result}"
        
    except Exception as e:
        return f"❌ Error searching GitHub issues: {str(e)}"


@tool
def github_get_directory_contents(directory_path: str = "", repository: str = None, branch: str = None) -> str:
    """Get contents of a directory in a GitHub repository.
    
    Args:
        directory_path: Path to the directory (empty string for root)
        repository: Repository name in format 'owner/repo' (default: from environment)
        branch: Branch to read from (default: from environment)
        
    Returns:
        Directory contents listing
    """
    try:
        toolkit = _get_github_toolkit(repository)
        if not toolkit:
            return "❌ Failed to initialize GitHub connection"
            
        # Get the directory tool
        tools = toolkit.get_tools()
        dir_tool = next((tool for tool in tools if "Get files from a directory" in tool.name), None)
        
        if not dir_tool:
            return "❌ Directory tool not found"
            
        # Execute the tool
        result = dir_tool.invoke({"directory_path": directory_path})
        
        return f"📁 **GitHub Directory Contents** (Repository: {repository or 'default'})\nPath: {directory_path or 'root'}\n\n{result}"
        
    except Exception as e:
        return f"❌ Error getting GitHub directory contents: {str(e)}"


@tool
def github_get_latest_release(repository: str = None) -> str:
    """Get the latest release from a GitHub repository.
    
    Args:
        repository: Repository name in format 'owner/repo' (default: from environment)
        
    Returns:
        Latest release information
    """
    try:
        toolkit = _get_github_toolkit(repository)
        if not toolkit:
            return "❌ Failed to initialize GitHub connection"
            
        # Get the latest release tool
        tools = toolkit.get_tools()
        release_tool = next((tool for tool in tools if "Get Latest Release" in tool.name), None)
        
        if not release_tool:
            return "❌ Latest release tool not found"
            
        # Execute the tool
        result = release_tool.invoke({})
        
        return f"🚀 **GitHub Latest Release** (Repository: {repository or 'default'})\n\n{result}"
        
    except Exception as e:
        return f"❌ Error getting GitHub latest release: {str(e)}"


@tool
def github_create_repository(name: str, description: str = "", private: bool = False, owner: str = "LimbicNode42") -> str:
    """Create a new GitHub repository.
    
    Args:
        name: Repository name
        description: Repository description (optional)
        private: Whether the repository should be private (default: False)
        owner: Repository owner (default: LimbicNode42)
        
    Returns:
        Details of the created repository
    """
    try:
        import os
        from github import Github
        
        # Initialize GitHub API client
        token = os.environ.get("GITHUB_APP_PRIVATE_KEY")
        app_id = os.environ.get("GITHUB_APP_ID")
        
        if not token or not app_id:
            return "❌ GitHub authentication not configured"
        
        # Create repository using PyGitHub directly since GitHubToolkit doesn't include repo creation
        g = Github(token)
        user = g.get_user(owner)
        
        repo = user.create_repo(
            name=name,
            description=description,
            private=private,
            auto_init=True  # Initialize with README
        )
        
        return f"✨ **GitHub Repository Created**\n" \
               f"Name: {repo.full_name}\n" \
               f"Description: {description}\n" \
               f"Private: {private}\n" \
               f"URL: {repo.html_url}\n" \
               f"Clone URL: {repo.clone_url}"
        
    except Exception as e:
        return f"❌ Error creating GitHub repository '{name}': {str(e)}"


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

def get_all_tools() -> List:
    """Get all available tools for agent initialization.
    
    Returns:
        List of all tool functions including handoff capabilities
    """
    return [
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
        
        # GitHub Integration
        github_get_issues, github_get_issue, github_comment_on_issue,
        github_list_pull_requests, github_get_pull_request, github_create_pull_request,
        github_create_file, github_read_file, github_update_file, github_delete_file,
        github_list_branches, github_create_branch, github_set_active_branch,
        github_search_code, github_search_issues, github_get_directory_contents,
        github_get_latest_release, github_create_repository,
        
        # Project Management
        create_task, update_task_status, get_team_workload,
        
        # Email & Communication (Leadership)
        send_email, schedule_meeting
    ]


def get_tool_descriptions() -> Dict[str, str]:
    """Get descriptions of all available tools for agent awareness.
    
    Returns:
        Dictionary mapping tool names to their descriptions
    """
    tools = get_all_tools()
    return {tool.name: tool.description for tool in tools}
