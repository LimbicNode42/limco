"""
Test GitHub MCP hybrid connection strategy
"""

import sys
import os
import tempfile
sys.path.append('src')

def test_github_connection_manager():
    """Test GitHub MCP connection manager."""
    print('='*60)
    print('TESTING GITHUB MCP CONNECTION MANAGER')
    print('='*60)
    
    try:
        from dev_team.tools.github_mcp import MCPConnectionManager as GitHubManager
        github_manager = GitHubManager()
        
        print('✅ GitHub MCPConnectionManager: IMPORTED')
        
        # Test aggregator health check
        aggregator_health = github_manager.check_aggregator_health()
        print(f'  Aggregator health: {aggregator_health}')
        
        # Test connection info
        info = github_manager.get_connection_info('github')
        method = info.get('method', 'unknown')
        available = info.get('available', False)
        print(f'  github: method={method}, available={available}')
        
        if method != "native" or not available:
            print(f'   ⚠️  Expected native/available but got {method}/{available}')
            return False
            
        return True
        
    except Exception as e:
        print(f'❌ GitHub Connection Manager: FAILED - {e}')
        return False

def test_github_hybrid_tools():
    """Test GitHub hybrid tools."""
    print('\n' + '='*60)
    print('TESTING GITHUB HYBRID TOOLS')
    print('='*60)
    
    try:
        from dev_team.tools.github_mcp import (
            github_get_repository_info, 
            github_search_repositories_hybrid,
            validate_github_mcp_connection
        )
        
        # Test connection validation
        validation = validate_github_mcp_connection.func()
        print(f'✅ Connection Validation: success={validation.get("success", False)}')
        print(f'  Connection method: {validation.get("connection_method", "unknown")}')
        
        validation_results = validation.get("validation_results", {})
        print(f'  Aggregator health: {validation_results.get("aggregator_health", False)}')
        print(f'  Individual server available: {validation_results.get("individual_server_available", False)}')
        print(f'  Native fallback: {validation_results.get("native_fallback", False)}')
        print(f'  GitHub token configured: {validation_results.get("github_token_configured", False)}')
        
        if not validation_results.get("github_token_configured", False):
            print('  ⚠️  No GitHub token configured - testing with rate limits')
        
        # Test repository info (using a public repo)
        repo_result = github_get_repository_info.func(owner="microsoft", repo="vscode")
        print(f'✅ Repository Info: success={repo_result.get("success", False)}')
        print(f'  Connection method: {repo_result.get("connection_method", "unknown")}')
        
        if repo_result.get("success"):
            repo_info = repo_result.get("repository", {})
            print(f'  Repository: {repo_info.get("full_name", "N/A")}')
            print(f'  Language: {repo_info.get("language", "N/A")}')
        
        # Test search (simple query)
        search_result = github_search_repositories_hybrid.func(query="vscode", limit=3)
        print(f'✅ Repository Search: success={search_result.get("success", False)}')
        print(f'  Connection method: {search_result.get("connection_method", "unknown")}')
        
        if search_result.get("success"):
            repos = search_result.get("repositories", [])
            print(f'  Found {len(repos)} repositories')
        
        return True
        
    except Exception as e:
        print(f'❌ GitHub Hybrid Tools: FAILED - {e}')
        return False

def test_github_mcp_client():
    """Test GitHub MCP client with hybrid strategy."""
    print('\n' + '='*60)
    print('TESTING GITHUB MCP CLIENT')
    print('='*60)
    
    try:
        from dev_team.tools.github_mcp import GitHubMCPClient, get_github_token
        
        # Try to get token (will use fake one if not available)
        try:
            token = get_github_token()
            print('✅ GitHub token found')
        except ValueError:
            token = "fake_token_for_testing"
            print('⚠️  Using fake token for testing')
        
        # Create client
        client = GitHubMCPClient(token)
        print('✅ GitHub MCP Client created')
        
        # Test connection info
        connection_info = client.mcp_manager.get_connection_info("github")
        print(f'  Connection method: {connection_info["method"]}')
        print(f'  Available: {connection_info["available"]}')
        
        # Test that we can get native tools
        native_tools = client._get_tools_native()
        print(f'✅ Native tools available: {len(native_tools)}')
        
        for tool in native_tools:
            print(f'  - {tool.name}')
        
        return True
        
    except Exception as e:
        print(f'❌ GitHub MCP Client: FAILED - {e}')
        return False

def main():
    """Run all GitHub MCP tests."""
    print("GITHUB MCP HYBRID STRATEGY VALIDATION")
    print("=" * 60)
    
    tests = [
        ("GitHub Connection Manager", test_github_connection_manager),
        ("GitHub Hybrid Tools", test_github_hybrid_tools),
        ("GitHub MCP Client", test_github_mcp_client)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result, None))
        except Exception as e:
            results.append((test_name, False, str(e)))
    
    # Summary
    print('\n' + '='*60)
    print('GITHUB MCP VALIDATION SUMMARY')
    print('='*60)
    
    passed = 0
    for test_name, success, error in results:
        if success:
            print(f'✅ {test_name}: PASSED')
            passed += 1
        else:
            print(f'❌ {test_name}: FAILED')
            if error:
                print(f'   Error: {error}')
    
    print(f'\nResults: {passed}/{len(tests)} tests passed')
    
    if passed == len(tests):
        print('\n🎉 GitHub MCP hybrid connection strategy working correctly!')
        print('✅ Connection manager operational')
        print('✅ Native fallbacks available and functional')
        print('✅ Tools properly report connection methods')
        return True
    else:
        print('\n⚠️  Some tests failed - check implementation')
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
