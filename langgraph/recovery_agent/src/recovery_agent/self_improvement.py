"""
Self-Improvement and Error Recovery System for Drive Recovery Agent.
Uses Claude 3.5 Sonnet to analyze errors, suggest fixes, and learn from failures.
"""

import os
import json
import platform
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage


class SelfImprovementEngine:
    """
    AI-powered self-improvement system that learns from errors and suggests fixes.
    """
    
    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.2
        )
        self.error_history = []
        self.solutions_database = {}
        self.load_knowledge_base()
    
    def load_knowledge_base(self):
        """Load existing knowledge base of errors and solutions."""
        kb_file = "error_solutions_kb.json"
        if os.path.exists(kb_file):
            try:
                with open(kb_file, 'r') as f:
                    self.solutions_database = json.load(f)
            except Exception as e:
                print(f"Could not load knowledge base: {e}")
    
    def save_knowledge_base(self):
        """Save updated knowledge base."""
        kb_file = "error_solutions_kb.json"
        try:
            with open(kb_file, 'w') as f:
                json.dump(self.solutions_database, f, indent=2)
        except Exception as e:
            print(f"Could not save knowledge base: {e}")
    
    def analyze_error_and_suggest_fixes(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze an error using Claude 3.5 Sonnet and suggest intelligent fixes.
        """
        error_type = error_context.get('error_type', 'unknown')
        error_message = error_context.get('error_message', '')
        system_info = error_context.get('system_info', {})
        operation_context = error_context.get('operation_context', {})
        
        # Check if we've seen this error before
        error_signature = self._generate_error_signature(error_context)
        if error_signature in self.solutions_database:
            cached_solution = self.solutions_database[error_signature]
            cached_solution['source'] = 'cached_knowledge'
            return cached_solution
        
        # Use LLM to analyze the error
        system_prompt = """You are an expert system administrator and data recovery specialist with deep knowledge of:
- Windows, Linux, and macOS system operations
- Drive cloning tools (dd, diskpart, etc.)
- Permission and access issues
- File system corruption patterns
- Recovery tool diagnostics

Analyze the provided error and suggest specific, actionable fixes ranked by likelihood of success."""

        user_prompt = f"""
ERROR ANALYSIS REQUEST:

Error Type: {error_type}
Error Message: {error_message}

System Information:
- OS: {system_info.get('os', 'unknown')}
- Platform: {system_info.get('platform', 'unknown')}
- User Privileges: {system_info.get('is_admin', 'unknown')}

Operation Context:
- Operation: {operation_context.get('operation', 'unknown')}
- Target: {operation_context.get('target', 'unknown')}
- Tool Used: {operation_context.get('tool', 'unknown')}

Previous Solutions Tried: {operation_context.get('attempted_solutions', [])}

Please provide:
1. Root cause analysis
2. 3-5 specific solutions ranked by success probability
3. Commands or steps to implement each solution
4. Preventive measures for future operations
5. Alternative approaches if primary solutions fail

Format as JSON with this structure:
{{
    "root_cause": "detailed analysis",
    "solutions": [
        {{
            "name": "solution name",
            "probability": "high/medium/low",
            "steps": ["step 1", "step 2", ...],
            "commands": ["command 1", "command 2", ...],
            "requirements": ["requirement 1", "requirement 2", ...],
            "risks": "potential risks",
            "expected_outcome": "what should happen"
        }}
    ],
    "preventive_measures": ["measure 1", "measure 2", ...],
    "alternative_approaches": ["approach 1", "approach 2", ...]
}}
"""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            
            # Parse the JSON response
            analysis = json.loads(response.content)
            
            # Add metadata
            analysis['timestamp'] = datetime.now().isoformat()
            analysis['error_signature'] = error_signature
            analysis['source'] = 'ai_analysis'
            
            # Cache the solution
            self.solutions_database[error_signature] = analysis
            self.save_knowledge_base()
            
            # Log to history
            self.error_history.append({
                'error_context': error_context,
                'analysis': analysis
            })
            
            return analysis
            
        except Exception as e:
            return {
                'root_cause': f'Failed to analyze error: {e}',
                'solutions': [{
                    'name': 'Manual troubleshooting required',
                    'probability': 'unknown',
                    'steps': ['Consult system administrator', 'Check system logs'],
                    'commands': [],
                    'requirements': [],
                    'risks': 'Unknown',
                    'expected_outcome': 'Manual resolution needed'
                }],
                'source': 'fallback'
            }
    
    def _generate_error_signature(self, error_context: Dict[str, Any]) -> str:
        """Generate a unique signature for this type of error."""
        error_type = error_context.get('error_type', 'unknown')
        operation = error_context.get('operation_context', {}).get('operation', 'unknown')
        os_type = error_context.get('system_info', {}).get('os', 'unknown')
        
        return f"{error_type}_{operation}_{os_type}".lower().replace(' ', '_')
    
    def suggest_improvement_for_workflow_node(self, node_name: str, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggest improvements for a specific workflow node that encountered an error.
        """
        system_prompt = """You are an expert in LangGraph workflows and error handling. 
Analyze the provided node error and suggest specific code improvements, better error handling, 
and workflow modifications."""

        user_prompt = f"""
NODE IMPROVEMENT REQUEST:

Node Name: {node_name}
Error Context: {json.dumps(error_context, indent=2)}

Please suggest:
1. Code improvements for this specific node
2. Better error handling strategies
3. Fallback mechanisms
4. Input validation improvements
5. User communication enhancements

Provide practical, implementable suggestions.
"""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            
            return {
                'node_name': node_name,
                'suggestions': response.content,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'node_name': node_name,
                'suggestions': f'Failed to generate suggestions: {e}',
                'timestamp': datetime.now().isoformat()
            }


class ErrorRecoveryHandler:
    """
    Handles automatic error recovery and solution implementation.
    """
    
    def __init__(self):
        self.improvement_engine = SelfImprovementEngine()
    
    def handle_drive_clone_error(self, error_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Specifically handle drive cloning errors with intelligent recovery.
        """
        system_info = {
            'os': platform.system(),
            'platform': platform.platform(),
            'is_admin': self._check_admin_privileges()
        }
        
        error_context = {
            'error_type': 'drive_clone_failure',
            'error_message': error_details.get('error', 'Unknown cloning error'),
            'system_info': system_info,
            'operation_context': {
                'operation': 'drive_cloning',
                'target': error_details.get('source_path', 'unknown'),
                'tool': 'dd' if system_info['os'] != 'Windows' else 'windows_clone',
                'attempted_solutions': error_details.get('attempted_solutions', [])
            }
        }
        
        # Get AI analysis and solutions
        analysis = self.improvement_engine.analyze_error_and_suggest_fixes(error_context)
        
        # Try to automatically implement solutions
        recovery_results = []
        for solution in analysis.get('solutions', [])[:2]:  # Try top 2 solutions
            if solution['probability'] in ['high', 'medium']:
                result = self._attempt_solution(solution, error_details)
                recovery_results.append(result)
                if result.get('success'):
                    break
        
        return {
            'analysis': analysis,
            'recovery_attempts': recovery_results,
            'success': any(r.get('success') for r in recovery_results)
        }
    
    def _check_admin_privileges(self) -> bool:
        """Check if running with admin privileges."""
        try:
            if platform.system() == 'Windows':
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin()
            else:
                return os.geteuid() == 0
        except:
            return False
    
    def _attempt_solution(self, solution: Dict[str, Any], error_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt to implement a suggested solution automatically.
        """
        solution_name = solution.get('name', 'Unknown')
        
        try:
            # Handle specific solution types
            if 'admin' in solution_name.lower() or 'privilege' in solution_name.lower():
                return self._handle_privilege_solution(solution, error_details)
            elif 'space' in solution_name.lower() or 'disk' in solution_name.lower():
                return self._handle_disk_space_solution(solution, error_details)
            elif 'alternative' in solution_name.lower() or 'tool' in solution_name.lower():
                return self._handle_alternative_tool_solution(solution, error_details)
            else:
                # Generic solution attempt
                return self._handle_generic_solution(solution, error_details)
                
        except Exception as e:
            return {
                'solution': solution_name,
                'success': False,
                'error': str(e),
                'message': f'Failed to implement solution: {e}'
            }
    
    def _handle_privilege_solution(self, solution: Dict[str, Any], error_details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle solutions related to privilege escalation."""
        if not self._check_admin_privileges():
            return {
                'solution': solution['name'],
                'success': False,
                'message': 'Please run as Administrator and try again',
                'user_action_required': True,
                'instructions': [
                    'Right-click on Command Prompt or PowerShell',
                    'Select "Run as Administrator"',
                    'Navigate to the recovery agent directory',
                    'Run the recovery agent again'
                ]
            }
        else:
            return {
                'solution': solution['name'],
                'success': True,
                'message': 'Admin privileges confirmed'
            }
    
    def _handle_disk_space_solution(self, solution: Dict[str, Any], error_details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle solutions related to disk space issues."""
        try:
            # Check available disk space
            clone_dir = error_details.get('clone_dir', os.path.expanduser('~/recovery_clones'))
            statvfs = os.statvfs(clone_dir) if hasattr(os, 'statvfs') else None
            
            if statvfs:
                free_space = statvfs.f_frsize * statvfs.f_bavail
                free_space_gb = free_space / (1024**3)
                
                return {
                    'solution': solution['name'],
                    'success': free_space_gb > 10,  # Assume we need at least 10GB
                    'message': f'Available space: {free_space_gb:.1f}GB',
                    'free_space_gb': free_space_gb
                }
            else:
                return {
                    'solution': solution['name'],
                    'success': False,
                    'message': 'Could not check disk space on Windows',
                    'user_action_required': True
                }
                
        except Exception as e:
            return {
                'solution': solution['name'],
                'success': False,
                'message': f'Error checking disk space: {e}'
            }
    
    def _handle_alternative_tool_solution(self, solution: Dict[str, Any], error_details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle solutions that suggest alternative tools."""
        # This would implement trying different cloning methods
        return {
            'solution': solution['name'],
            'success': False,
            'message': 'Alternative tool solutions not yet implemented',
            'suggestion': 'Consider using imaging software like Win32 Disk Imager for Windows'
        }
    
    def _handle_generic_solution(self, solution: Dict[str, Any], error_details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic solutions."""
        return {
            'solution': solution['name'],
            'success': False,
            'message': 'Generic solution - manual implementation required',
            'steps': solution.get('steps', [])
        }


# Integration functions for the main recovery workflow
def enhance_node_with_self_improvement(node_function):
    """
    Decorator to add self-improvement capabilities to any workflow node.
    """
    def enhanced_node(state):
        error_handler = ErrorRecoveryHandler()
        
        try:
            # Execute original node
            result = node_function(state)
            
            # Check for errors in result
            if result.get('error'):
                # Analyze error and suggest improvements
                recovery_result = error_handler.handle_drive_clone_error({
                    'error': result['error'],
                    'source_path': state.get('selected_drive'),
                    'clone_dir': os.path.expanduser('~/recovery_clones')
                })
                
                # Add recovery information to state
                result['recovery_analysis'] = recovery_result['analysis']
                result['recovery_attempts'] = recovery_result['recovery_attempts']
                
                # Update error message with intelligent suggestions
                if recovery_result['analysis'].get('solutions'):
                    top_solution = recovery_result['analysis']['solutions'][0]
                    result['error_with_suggestions'] = f"""
{result['error']}

🤖 AI Analysis: {recovery_result['analysis']['root_cause']}

💡 Suggested Fix ({top_solution['probability']} probability):
{top_solution['name']}

Steps to try:
{chr(10).join(f"• {step}" for step in top_solution['steps'])}

Requirements: {', '.join(top_solution.get('requirements', []))}
"""
            
            return result
            
        except Exception as e:
            # If the node itself fails, analyze that error too
            error_context = {
                'error_type': 'node_execution_failure',
                'error_message': str(e),
                'node_name': node_function.__name__
            }
            
            improvement_suggestion = error_handler.improvement_engine.suggest_improvement_for_workflow_node(
                node_function.__name__, error_context
            )
            
            return {
                'error': str(e),
                'improvement_suggestion': improvement_suggestion,
                'messages': state.get('messages', [])
            }
    
    return enhanced_node
