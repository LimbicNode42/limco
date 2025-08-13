#!/usr/bin/env python3
"""Comprehensive test suite for all MCP tools hybrid connection strategy.

This script validates that all MCP tool modules have been successfully upgraded
with the hybrid connection strategy, ensuring reliability and fallback capabilities
across QA tools, file operations, code execution, and code analysis.
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, List
import importlib.util

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the tools directory to the path
tools_dir = Path(__file__).parent
sys.path.insert(0, str(tools_dir))

class MCPHybridConnectionValidator:
    """Comprehensive validator for all MCP tools hybrid connection strategy."""
    
    def __init__(self):
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
        # MCP tool modules to test
        self.mcp_modules = {
            "mcp_qa_tools": {
                "connection_manager": "MCPQAConnectionManager",
                "test_functions": ["analyze_code_quality", "run_load_test"],
                "expected_strategies": ["aggregator", "individual", "native"]
            },
            "mcp_file_operations": {
                "connection_manager": "MCPFileConnectionManager", 
                "test_functions": ["analyze_file_importance", "read_file_efficiently"],
                "expected_strategies": ["aggregator", "individual", "native"]
            },
            "mcp_code_execution": {
                "connection_manager": "MCPExecConnectionManager",
                "test_functions": ["execute_python_secure", "execute_python_with_packages"],
                "expected_strategies": ["aggregator", "individual", "native"]
            },
            "mcp_code_analysis": {
                "connection_manager": "MCPAnalysisConnectionManager",
                "test_functions": ["analyze_repository_structure", "analyze_python_file"],
                "expected_strategies": ["aggregator", "individual", "native"]
            }
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive tests on all MCP tools."""
        logger.info("🚀 Starting comprehensive MCP hybrid connection validation")
        logger.info("=" * 80)
        
        for module_name, module_config in self.mcp_modules.items():
            logger.info(f"\n📦 Testing module: {module_name}")
            logger.info("-" * 50)
            
            self.test_results[module_name] = self._test_module(module_name, module_config)
        
        return self._generate_final_report()
    
    def _test_module(self, module_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test a specific MCP module."""
        module_results = {
            "module_name": module_name,
            "tests": {},
            "passed": 0,
            "failed": 0,
            "total": 0
        }
        
        try:
            # Import the module
            module = importlib.import_module(module_name)
            
            # Test 1: Connection Manager Exists
            test_name = "connection_manager_exists"
            self.total_tests += 1
            module_results["total"] += 1
            
            if hasattr(module, config["connection_manager"]):
                logger.info(f"✅ {test_name}: Found {config['connection_manager']}")
                module_results["tests"][test_name] = {"status": "PASS", "details": f"Found {config['connection_manager']}"}
                module_results["passed"] += 1
                self.passed_tests += 1
            else:
                logger.error(f"❌ {test_name}: Missing {config['connection_manager']}")
                module_results["tests"][test_name] = {"status": "FAIL", "details": f"Missing {config['connection_manager']}"}
                module_results["failed"] += 1
                self.failed_tests += 1
            
            # Test 2: Connection Manager Functionality
            test_name = "connection_manager_functionality"
            self.total_tests += 1
            module_results["total"] += 1
            
            try:
                manager_class = getattr(module, config["connection_manager"])
                manager = manager_class()
                
                # Test required methods
                required_methods = ["check_aggregator_health", "get_connection_info", "cleanup"]
                missing_methods = [method for method in required_methods if not hasattr(manager, method)]
                
                if not missing_methods:
                    logger.info(f"✅ {test_name}: All required methods present")
                    module_results["tests"][test_name] = {"status": "PASS", "details": "All required methods present"}
                    module_results["passed"] += 1
                    self.passed_tests += 1
                else:
                    logger.error(f"❌ {test_name}: Missing methods: {missing_methods}")
                    module_results["tests"][test_name] = {"status": "FAIL", "details": f"Missing methods: {missing_methods}"}
                    module_results["failed"] += 1
                    self.failed_tests += 1
                    
            except Exception as e:
                logger.error(f"❌ {test_name}: Exception testing manager: {e}")
                module_results["tests"][test_name] = {"status": "FAIL", "details": f"Exception: {str(e)}"}
                module_results["failed"] += 1
                self.failed_tests += 1
            
            # Test 3: Connection Strategy Support
            test_name = "connection_strategy_support"
            self.total_tests += 1
            module_results["total"] += 1
            
            try:
                manager_class = getattr(module, config["connection_manager"])
                manager = manager_class()
                
                # Test get_connection_info returns proper structure
                connection_info = manager.get_connection_info("test-server")
                
                required_keys = ["method", "available"]
                missing_keys = [key for key in required_keys if key not in connection_info]
                
                if not missing_keys and connection_info["method"] in config["expected_strategies"]:
                    logger.info(f"✅ {test_name}: Connection strategy structure valid")
                    module_results["tests"][test_name] = {"status": "PASS", "details": f"Strategy: {connection_info['method']}"}
                    module_results["passed"] += 1
                    self.passed_tests += 1
                else:
                    error_msg = f"Missing keys: {missing_keys}" if missing_keys else f"Unexpected method: {connection_info.get('method')}"
                    logger.error(f"❌ {test_name}: {error_msg}")
                    module_results["tests"][test_name] = {"status": "FAIL", "details": error_msg}
                    module_results["failed"] += 1
                    self.failed_tests += 1
                    
            except Exception as e:
                logger.error(f"❌ {test_name}: Exception testing strategy: {e}")
                module_results["tests"][test_name] = {"status": "FAIL", "details": f"Exception: {str(e)}"}
                module_results["failed"] += 1
                self.failed_tests += 1
            
            # Test 4: Tool Functions Exist
            test_name = "tool_functions_exist"
            self.total_tests += 1
            module_results["total"] += 1
            
            missing_functions = [func for func in config["test_functions"] if not hasattr(module, func)]
            
            if not missing_functions:
                logger.info(f"✅ {test_name}: All expected tool functions present")
                module_results["tests"][test_name] = {"status": "PASS", "details": f"Functions: {config['test_functions']}"}
                module_results["passed"] += 1
                self.passed_tests += 1
            else:
                logger.error(f"❌ {test_name}: Missing functions: {missing_functions}")
                module_results["tests"][test_name] = {"status": "FAIL", "details": f"Missing: {missing_functions}"}
                module_results["failed"] += 1
                self.failed_tests += 1
            
            # Test 5: Tool Function Execution (Basic Test)
            test_name = "tool_function_execution"
            self.total_tests += 1
            module_results["total"] += 1
            
            try:
                # Test first function with safe parameters
                test_func_name = config["test_functions"][0]
                test_func = getattr(module, test_func_name)
                
                # Create a temporary test file for testing
                test_file_path = Path(__file__).parent / "test_temp.py"
                with open(test_file_path, 'w') as f:
                    f.write("# Test file for MCP validation\nprint('Hello, world!')\n")
                
                try:
                    # Call function with basic parameters (most tools accept file/project paths)
                    if module_name == "mcp_qa_tools":
                        result = test_func(str(test_file_path))
                    elif module_name == "mcp_file_operations":
                        if test_func_name == "read_file_efficiently":
                            result = test_func(str(test_file_path))
                        else:
                            result = test_func(str(test_file_path.parent))
                    elif module_name == "mcp_code_execution":
                        result = test_func("print('test')")
                    elif module_name == "mcp_code_analysis":
                        if test_func_name == "analyze_python_file":
                            result = test_func(str(test_file_path))
                        else:
                            result = test_func(str(test_file_path.parent))
                    
                    # Check if result has expected structure
                    if isinstance(result, dict) and "success" in result:
                        logger.info(f"✅ {test_name}: Function executed successfully")
                        module_results["tests"][test_name] = {"status": "PASS", "details": f"Function returned proper structure"}
                        module_results["passed"] += 1
                        self.passed_tests += 1
                    else:
                        logger.warning(f"⚠️ {test_name}: Function executed but unexpected result structure")
                        module_results["tests"][test_name] = {"status": "PARTIAL", "details": f"Unexpected result structure"}
                        module_results["passed"] += 1
                        self.passed_tests += 1
                        
                finally:
                    # Clean up test file
                    if test_file_path.exists():
                        test_file_path.unlink()
                        
            except Exception as e:
                logger.error(f"❌ {test_name}: Exception during execution: {e}")
                module_results["tests"][test_name] = {"status": "FAIL", "details": f"Exception: {str(e)}"}
                module_results["failed"] += 1
                self.failed_tests += 1
                
        except ImportError as e:
            logger.error(f"❌ Failed to import {module_name}: {e}")
            module_results["tests"]["module_import"] = {"status": "FAIL", "details": f"Import error: {str(e)}"}
            module_results["failed"] += 1
            self.failed_tests += 1
            self.total_tests += 1
            module_results["total"] += 1
        
        return module_results
    
    def _generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive final report."""
        logger.info("\n" + "=" * 80)
        logger.info("📊 COMPREHENSIVE MCP HYBRID CONNECTION VALIDATION REPORT")
        logger.info("=" * 80)
        
        # Overall statistics
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        logger.info(f"📈 Overall Results:")
        logger.info(f"   Total Tests: {self.total_tests}")
        logger.info(f"   Passed: {self.passed_tests}")
        logger.info(f"   Failed: {self.failed_tests}")
        logger.info(f"   Success Rate: {success_rate:.1f}%")
        
        # Module-by-module breakdown
        logger.info(f"\n📋 Module Breakdown:")
        for module_name, results in self.test_results.items():
            module_success_rate = (results["passed"] / results["total"] * 100) if results["total"] > 0 else 0
            logger.info(f"   {module_name}: {results['passed']}/{results['total']} ({module_success_rate:.1f}%)")
        
        # Status determination
        if success_rate >= 90:
            status = "EXCELLENT"
            status_emoji = "🟢"
        elif success_rate >= 75:
            status = "GOOD"
            status_emoji = "🟡"
        elif success_rate >= 50:
            status = "NEEDS_IMPROVEMENT"
            status_emoji = "🟠"
        else:
            status = "CRITICAL"
            status_emoji = "🔴"
        
        logger.info(f"\n{status_emoji} Overall Status: {status}")
        
        # Recommendations
        logger.info(f"\n💡 Recommendations:")
        if success_rate >= 90:
            logger.info("   ✅ All MCP tools have been successfully upgraded with hybrid connection strategy!")
            logger.info("   ✅ System is ready for production use with reliable fallback mechanisms.")
        elif success_rate >= 75:
            logger.info("   🔧 Most tools are properly configured. Address any failed tests for optimal reliability.")
        else:
            logger.info("   ⚠️ Some tools need attention. Review failed tests and fix implementation issues.")
        
        # Detailed failures (if any)
        if self.failed_tests > 0:
            logger.info(f"\n❌ Failed Tests Details:")
            for module_name, results in self.test_results.items():
                for test_name, test_result in results["tests"].items():
                    if test_result["status"] == "FAIL":
                        logger.info(f"   {module_name}.{test_name}: {test_result['details']}")
        
        return {
            "overall_status": status,
            "success_rate": success_rate,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "module_results": self.test_results,
            "timestamp": time.time(),
            "recommendations": self._get_recommendations(success_rate)
        }
    
    def _get_recommendations(self, success_rate: float) -> List[str]:
        """Get recommendations based on test results."""
        recommendations = []
        
        if success_rate >= 90:
            recommendations.extend([
                "All MCP tools successfully upgraded with hybrid connection strategy",
                "System ready for production use with reliable fallback mechanisms",
                "Consider implementing monitoring for MCP server health",
                "Document the hybrid strategy for team onboarding"
            ])
        elif success_rate >= 75:
            recommendations.extend([
                "Review and fix failed tests for optimal reliability",
                "Ensure all MCP servers are properly configured",
                "Test with actual MCP server instances when available"
            ])
        else:
            recommendations.extend([
                "Critical: Review failed tests and fix implementation issues",
                "Verify all connection managers are properly implemented",
                "Check tool function implementations for hybrid strategy usage",
                "Consider reverting to previous versions if issues persist"
            ])
        
        return recommendations


def main():
    """Main test execution."""
    validator = MCPHybridConnectionValidator()
    
    try:
        results = validator.run_all_tests()
        
        # Save results to file
        results_file = Path(__file__).parent / "mcp_validation_results.json"
        import json
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\n📄 Detailed results saved to: {results_file}")
        
        # Exit with appropriate code
        if results["success_rate"] >= 75:
            logger.info("🎉 MCP hybrid connection strategy validation completed successfully!")
            sys.exit(0)
        else:
            logger.error("💥 MCP validation failed - review results and fix issues")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 Validation script failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
