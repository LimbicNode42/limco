"""Tools module for development team agents.

This module provides a clean interface to all available tools organized by category.
"""

from .agent_handoffs import *
from .research_communication import *
from .filesystem_code import *
from .code_review_quality import *
from .github_integration import *

# Import MCP tools
from .mcp_code_execution import *
from .mcp_code_analysis import *
from .mcp_file_operations import *
from .mcp_qa_tools import *


def get_all_tools():
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
        
        # Filesystem & Code
        read_file, write_file, list_files,
        
        # Code Development & Quality
        run_code, run_tests, run_static_analysis, run_security_scan, 
        run_code_quality_check, request_copilot_review,
        
        # MCP Code Execution Tools
        execute_python_secure, execute_python_with_packages, create_virtual_environment,
        list_virtual_environments,
        
        # MCP Code Analysis Tools
        analyze_repository_structure, analyze_python_file,
        
        # MCP File Operations Tools
        analyze_file_importance, read_file_efficiently, edit_file_at_line,
        edit_file_range, get_language_server_info, clear_file_cache,
        
        # MCP QA & Testing Tools
        analyze_code_quality, run_load_test, create_load_test_script,
        validate_test_environment,
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


def get_tool_descriptions():
    """Get descriptions of all available tools for agent awareness.
    
    Returns:
        Dictionary mapping tool names to their descriptions
    """
    tools = get_all_tools()
    return {tool.name: tool.description for tool in tools}


__all__ = [
    'get_all_tools',
    'get_tool_descriptions',
    
    # Agent Handoffs
    'transfer_to_qa_engineer', 'escalate_to_cto', 'request_peer_review',
    'delegate_to_engineering_manager', 'transfer_to_senior_engineer', 'escalate_to_human',
    
    # Research & Communication
    'web_search', 'web_search_news', 'web_search_academic',
    
    # Filesystem & Code
    'read_file', 'write_file', 'list_files',
    
    # Code Development & Quality
    'run_code', 'run_tests', 'run_static_analysis', 'run_security_scan',
    'run_code_quality_check', 'request_copilot_review',
    
    # GitHub Integration
    'get_github_mcp_tools_sync',
    
    # MCP Code Execution Tools
    'execute_python_secure', 'execute_python_with_packages', 'create_virtual_environment',
    'list_virtual_environments',
    
    # MCP Code Analysis Tools
    'analyze_repository_structure', 'analyze_python_file',
    
    # MCP File Operations Tools
    'analyze_file_importance', 'read_file_efficiently', 'edit_file_at_line',
    'edit_file_range', 'get_language_server_info', 'clear_file_cache',
    
    # MCP QA & Testing Tools
    'analyze_code_quality', 'run_load_test', 'create_load_test_script',
    'validate_test_environment',
]
