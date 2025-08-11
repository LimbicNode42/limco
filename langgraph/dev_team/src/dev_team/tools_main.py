"""Main tools module providing centralized access to all development team tools.

This module serves as the central hub for all tools available to development team agents.
Tools are organized by category in separate modules for better maintainability.
"""

from typing import List
from .tools import (
    # Agent Handoffs
    transfer_to_qa_engineer, escalate_to_cto, request_peer_review,
    delegate_to_engineering_manager, transfer_to_senior_engineer, escalate_to_human,
    
    # Research & Communication
    web_search, web_search_news, web_search_academic,
    
    # Document Management
    search_documents, create_document, update_document,
    
    # Database & Data
    query_database, get_project_metrics,
    
    # Filesystem & Code
    read_file, write_file, list_files,
    
    # Code Development & Quality
    run_code, run_tests, run_static_analysis, run_security_scan,
    run_code_quality_check, request_copilot_review,
    
    # Project Management
    create_task, update_task_status, get_team_workload,
    
    # GitHub Integration
    get_github_mcp_tools_sync,
)


def get_all_tools() -> List:
    """Get all available tools for agent initialization.
    
    Returns:
        List of all tool functions including handoff capabilities
    """
    base_tools = [
        # Agent Handoff & Collaboration
        transfer_to_qa_engineer, escalate_to_cto, request_peer_review,
        delegate_to_engineering_manager, transfer_to_senior_engineer, escalate_to_human,
        
        # Research & Communication
        web_search, web_search_news, web_search_academic,
        
        # Document & Knowledge Management
        search_documents, create_document, update_document,
        
        # Database & Data
        query_database, get_project_metrics,
        
        # Filesystem & Code
        read_file, write_file, list_files,
        
        # Code Development & Quality
        run_code, run_tests, run_static_analysis, run_security_scan, 
        run_code_quality_check, request_copilot_review,
        
        # Project Management
        create_task, update_task_status, get_team_workload
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


def get_tool_descriptions() -> dict:
    """Get descriptions of all available tools for agent awareness.
    
    Returns:
        Dictionary mapping tool names to their descriptions
    """
    tools = get_all_tools()
    return {tool.name: tool.description for tool in tools}


# Export commonly used tools for direct access
__all__ = [
    'get_all_tools',
    'get_tool_descriptions',
    
    # Tool categories for direct import if needed
    'transfer_to_qa_engineer', 'escalate_to_cto', 'request_peer_review',
    'delegate_to_engineering_manager', 'transfer_to_senior_engineer', 'escalate_to_human',
    'web_search', 'web_search_news', 'web_search_academic',
    'search_documents', 'create_document', 'update_document',
    'query_database', 'get_project_metrics',
    'read_file', 'write_file', 'list_files',
    'run_code', 'run_tests', 'run_static_analysis', 'run_security_scan',
    'run_code_quality_check', 'request_copilot_review',
    'create_task', 'update_task_status', 'get_team_workload',
]
