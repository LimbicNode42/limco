import sys
sys.path.append('src')

print('='*60)
print('TESTING MCP CONNECTION MANAGERS')
print('='*60)

modules = [
    ('File Operations', 'dev_team.tools.mcp_file_operations'),
    ('Code Execution', 'dev_team.tools.mcp_code_execution'), 
    ('Code Analysis', 'dev_team.tools.mcp_code_analysis'),
    ('QA Tools', 'dev_team.tools.mcp_qa_tools')
]

all_working = True

for name, module_name in modules:
    try:
        module = __import__(module_name, fromlist=['MCPConnectionManager'])
        if hasattr(module, 'MCPConnectionManager'):
            manager = module.MCPConnectionManager()
            print(f'✅ {name}: MCPConnectionManager available')
            
            # Test basic functionality
            health = manager.check_aggregator_health()
            print(f'   Aggregator health: {health}')
            
            # Test connection info with fallback to native
            info = manager.get_connection_info('test')
            method = info.get('method', 'unknown')
            available = info.get('available', False)
            print(f'   Connection method: {method}')
            print(f'   Available: {available}')
            
            if method != 'native' or not available:
                print(f'   ⚠️  Expected native/available but got {method}/{available}')
                all_working = False
                
        else:
            print(f'❌ {name}: MCPConnectionManager not found')
            all_working = False
    except Exception as e:
        print(f'❌ {name}: Error - {e}')
        all_working = False

if all_working:
    print('\n🎉 All MCP Connection Managers are working!')
else:
    print('\n⚠️  Some connection managers need fixes')
