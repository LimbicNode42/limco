#!/usr/bin/env python
import sys
import warnings
import os
from datetime import datetime
from pathlib import Path
from limco.crew import Limco
from limco.utils.rate_limited_crew import create_rate_limited_crew
import logging

# Configure logging for rate limiting feedback
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Look for .env file in project root (parent of src directory)
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)
    print(f"🔧 Loaded environment from: {env_path}")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    print("🔧 Attempting to load environment variables from system...")

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")

# Suppress AgentOps warnings if not configured
try:
    import os
    if not os.getenv("AGENTOPS_API_KEY"):
        os.environ["AGENTOPS_API_KEY"] = "disabled"
        os.environ["AGENTOPS_ENABLED"] = "false"
except Exception:
    pass

# Global variables for rate limiting configuration
_run_aggressive_mode = False

def get_test_aggressive_mode():
    """Get the current test aggressive mode setting."""
    global _test_aggressive_mode
    return _test_aggressive_mode

def set_test_aggressive_mode(value):
    """Set the test aggressive mode setting."""
    global _test_aggressive_mode
    _test_aggressive_mode = value

# Default test mode
_test_aggressive_mode = True  # Default to aggressive for testing

def run():
    """
    Run the autonomous software development crew.
    
    This will execute the complete 5-phase development process:
    1. Goal Intake & Initial Planning
    2. Technical Planning & Estimation
    3. Business Analysis & Cost Planning
    4. Quality & Operations Planning
    5. Implementation Coordination
    
    The crew will generate an executive summary for CEO approval.
    """
    
    # Default example goal - replace with actual CEO input
    default_ceo_goal = """
    Build a SaaS platform for small businesses to manage their customer relationships 
    and automate their sales processes. The platform should include:
    - Customer contact management
    - Sales pipeline tracking
    - Email automation and templates
    - Basic reporting and analytics
    - Mobile-responsive web interface
    
    Target market: Small businesses (5-50 employees) in service industries.
    Budget: $50,000 maximum development cost.
    Timeline: Launch MVP within 3 months.
    Revenue target: $10,000 MRR within 6 months of launch.
    """
    
    # Get CEO goal from command line argument or use default
    ceo_goal = sys.argv[1] if len(sys.argv) > 1 else default_ceo_goal
    
    print(f"🚀 Starting Limco Autonomous Software Development Company")
    print(f"📋 CEO Goal: {ceo_goal[:100]}...")
    print(f"📅 Current Year: {datetime.now().year}")
    print("="*80)
    
    inputs = {
        'ceo_goal': ceo_goal,
        'current_year': str(datetime.now().year),
        'company_name': 'Limco',
        'ceo_name': 'LimbicNode42'
    }
    
    try:
        # Create standard crew
        crew = Limco().crew()
        
        # Wrap with rate limiting (conservative mode for API limits)
        aggressive_mode = _run_aggressive_mode
        rate_limited_crew = create_rate_limited_crew(crew, aggressive_mode=aggressive_mode)
        
        mode_desc = "Aggressive (faster)" if aggressive_mode else "Conservative (safer)"
        delays = "3s delays, 6 retries" if aggressive_mode else "5s delays, 8 retries"
        print(f"🛡️ Rate limiting enabled: {mode_desc} ({delays})")
        if not aggressive_mode:
            print("⏱️ This may take longer but will handle API rate limits gracefully")
        print("="*80)
        
        result = rate_limited_crew.kickoff(inputs)
        
        print("\n" + "="*80)
        print("✅ Autonomous development planning completed!")
        print("📄 Executive summary saved to: executive_summary.md")
        print("🎯 Ready for CEO review and approval")
        
        return result
        
    except Exception as e:
        print(f"❌ An error occurred while running the crew: {e}")
        print("💡 Consider:")
        print("   - Checking your API key balance")
        print("   - Using a simpler goal for testing")
        print("   - Waiting a few minutes before retrying")
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    Usage: python -m limco.main train <iterations> <filename>
    """
    if len(sys.argv) < 3:
        print("Usage: python -m limco.main train <iterations> <filename>")
        sys.exit(1)
        
    iterations = int(sys.argv[1])
    filename = sys.argv[2]
    
    default_ceo_goal = """
    Create a task management application for remote teams with real-time collaboration, 
    project tracking, and team communication features.
    """
    
    inputs = {
        'ceo_goal': default_ceo_goal,
        'current_year': str(datetime.now().year),
        'company_name': 'Limco',
        'ceo_name': 'LimbicNode42'
    }
    
    try:
        # Create crew and wrap with rate limiting for training
        crew = Limco().crew()
        rate_limited_crew = create_rate_limited_crew(crew, aggressive_mode=False)
        
        print(f"🎯 Training with rate limiting: {iterations} iterations")
        print("🛡️ Using conservative rate limiting for training stability")
        print("⏱️ This will take longer but prevent API rate limit issues")
        print("="*60)
        
        result = rate_limited_crew.train(iterations, filename, inputs)
        print(f"✅ Training completed for {iterations} iterations")
        return result
        
    except Exception as e:
        print(f"❌ An error occurred while training the crew: {e}")
        print("💡 Training requires significant API usage - consider:")
        print("   - Using fewer iterations")
        print("   - Checking API quota limits")
        print("   - Training during off-peak hours")
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    Usage: python -m limco.main replay <task_id>
    """
    if len(sys.argv) < 2:
        print("Usage: python -m limco.main replay <task_id>")
        sys.exit(1)
        
    task_id = sys.argv[1]
    
    try:
        Limco().crew().replay(task_id=task_id)
        print(f"✅ Replay completed for task: {task_id}")
        
    except Exception as e:
        print(f"❌ An error occurred while replaying the crew: {e}")
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test_basic():
    """
    Basic functionality test - just check imports and configuration.
    """
    try:
        print("🧪 Testing basic Limco functionality...")
        print("🔧 Checking imports...")
        
        from limco.crew import Limco
        from limco.utils.rate_limited_crew import create_rate_limited_crew
        from limco.utils.rate_limiter import RateLimiter
        
        print("✅ All imports successful")
        
        print("🔧 Checking environment...")
        import os
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        google_key = os.getenv("GOOGLE_API_KEY", "")
        serper_key = os.getenv("SERPER_API_KEY", "")
        
        print(f"🔑 Anthropic API: {'✅ Configured' if anthropic_key else '❌ Missing'}")
        print(f"🔑 Google API: {'✅ Configured' if google_key else '❌ Missing'}")  
        print(f"🔑 Serper API: {'✅ Configured' if serper_key else '⚠️ Optional'}")
        
        print("🔧 Testing rate limiter configuration...")
        rate_limiter = RateLimiter()
        print(f"✅ Rate limiter: {rate_limiter.base_delay}s delays, {rate_limiter.max_retries} retries")
        
        print("🔧 Testing crew creation...")
        crew = Limco().crew()
        print(f"✅ Crew created with {len(crew.agents)} agents")
        
        rate_limited_crew = create_rate_limited_crew(crew, aggressive_mode=False)
        print("✅ Rate-limited crew wrapper created")
        
        print("🎉 All basic functionality tests passed!")
        print("💡 Ready to run 'test-safe' for full testing")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        print("🔧 Please check your configuration and API keys")
        return False


def test():
    """
    Test the crew with a simple goal to verify functionality.
    """
    test_goal = """
    Build a simple web application that displays a list of tasks 
    with the ability to add, edit, and delete tasks. Use modern 
    web technologies and ensure mobile responsiveness.
    """
    
    print("🧪 Testing Limco crew with simple goal...")
    
    inputs = {
        'ceo_goal': test_goal,
        'current_year': str(datetime.now().year),
        'company_name': 'Limco',
        'ceo_name': 'LimbicNode42'
    }
    
    try:
        # Create standard crew
        crew = Limco().crew()
        
        # Use aggressive mode for testing (faster but still rate limited)
        aggressive_mode = get_test_aggressive_mode()
        rate_limited_crew = create_rate_limited_crew(crew, aggressive_mode=aggressive_mode)
        
        mode_desc = "Aggressive (faster)" if aggressive_mode else "Conservative (safer)"  
        delays = "3s delays, 6 retries" if aggressive_mode else "5s delays, 8 retries"
        print(f"🛡️ Rate limiting enabled: Test mode ({delays})")
        if aggressive_mode:
            print("⚡ Using faster settings for testing")
        else:
            print("🐌 Using conservative settings for testing")
        print("="*60)
        
        result = rate_limited_crew.kickoff(inputs)
        print("✅ Test completed successfully!")
        return result
        
    except Exception as e:
        error_msg = str(e).lower()
        if any(term in error_msg for term in ['overloaded', 'rate limit', '429', '529', 'quota']):
            print(f"⏰ API Rate Limit Hit: {e}")
            print("💡 The AI service is overloaded or you've hit rate limits")
            print("🔄 This is expected behavior - the rate limiter is working correctly")
            print("✅ Solutions:")
            print("   1. Wait 5-10 minutes and try again")
            print("   2. Try 'test-safe' for more conservative rate limiting") 
            print("   3. Consider upgrading to a premium API account for higher limits")
        else:
            print(f"❌ Test failed: {e}")
            print("💡 This might be a configuration or network issue")
        
        print("🔧 Troubleshooting tips:")
        print("   - Check your API keys are valid")
        print("   - Verify internet connection")  
        print("   - Review the full error above for specific details")
        raise Exception(f"An error occurred while testing the crew: {e}")
    """
    Test the crew with a simple goal to verify functionality.
    """
    test_goal = """
    Build a simple web application that displays a list of tasks 
    with the ability to add, edit, and delete tasks. Use modern 
    web technologies and ensure mobile responsiveness.
    """
    
    print("🧪 Testing Limco crew with simple goal...")
    
    inputs = {
        'ceo_goal': test_goal,
        'current_year': str(datetime.now().year),
        'company_name': 'Limco',
        'ceo_name': 'LimbicNode42'
    }
    
    try:
        # Create standard crew
        crew = Limco().crew()
        
        # Use aggressive mode for testing (faster but still rate limited)
        aggressive_mode = get_test_aggressive_mode()
        rate_limited_crew = create_rate_limited_crew(crew, aggressive_mode=aggressive_mode)
        
        mode_desc = "Aggressive (faster)" if aggressive_mode else "Conservative (safer)"  
        delays = "3s delays, 6 retries" if aggressive_mode else "5s delays, 8 retries"
        print(f"🛡️ Rate limiting enabled: Test mode ({delays})")
        if aggressive_mode:
            print("⚡ Using faster settings for testing")
        else:
            print("🐌 Using conservative settings for testing")
        print("="*60)
        
        result = rate_limited_crew.kickoff(inputs)
        print("✅ Test completed successfully!")
        return result
        
    except Exception as e:
        error_msg = str(e).lower()
        if any(term in error_msg for term in ['overloaded', 'rate limit', '429', '529', 'quota']):
            print(f"⏰ API Rate Limit Hit: {e}")
            print("💡 The AI service is overloaded or you've hit rate limits")
            print("🔄 This is expected behavior - the rate limiter is working correctly")
            print("✅ Solutions:")
            print("   1. Wait 5-10 minutes and try again")
            print("   2. Try 'test-safe' for more conservative rate limiting") 
            print("   3. Consider upgrading to a premium API account for higher limits")
        else:
            print(f"❌ Test failed: {e}")
            print("💡 This might be a configuration or network issue")
        
        print("🔧 Troubleshooting tips:")
        print("   - Check your API keys are valid")
        print("   - Verify internet connection")  
        print("   - Review the full error above for specific details")
        raise Exception(f"An error occurred while testing the crew: {e}")


if __name__ == "__main__":
    """
    Command line interface for Limco Autonomous Software Development Company
    
    Commands:
    - run [goal]: Execute development planning process (default)
    - run-fast [goal]: Execute with aggressive rate limiting (faster but may hit limits)
    - train <iterations> <filename>: Train the crew with rate limiting
    - replay <task_id>: Replay from a specific task  
    - test: Test with a simple goal (uses aggressive rate limiting)
    - test-safe: Test with conservative rate limiting
    """
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "train":
            # Remove command from args for train function
            sys.argv = sys.argv[1:]
            train()
        elif command == "replay":
            # Remove command from args for replay function  
            sys.argv = sys.argv[1:]
            replay()
        elif command == "test":
            test()
        elif command == "test-basic":
            test_basic()
        elif command == "test-safe":
            # Test with conservative rate limiting
            print("🐌 Using conservative rate limiting for testing")
            # Temporarily modify test function behavior
            set_test_aggressive_mode(False)
            test()
        elif command == "run":
            # Remove command and use remaining as goal
            sys.argv = sys.argv[1:]
            run()
        elif command == "run-fast":
            # Run with aggressive rate limiting
            sys.argv = sys.argv[1:]  # Remove command
            print("⚡ Using aggressive rate limiting (faster but may hit API limits)")
            _run_aggressive_mode = True
            run()
        elif command in ["help", "--help", "-h"]:
            print("""
Limco - Autonomous Software Development Company

Commands:
  run [goal]              Execute development planning (default, conservative rate limiting)
  run-fast [goal]         Execute with aggressive rate limiting (faster, for premium APIs)
  test                    Test with simple goal (aggressive rate limiting)
  test-safe               Test with conservative rate limiting (safer)
  test-basic              Basic functionality test (imports, config, no API calls)
  train <iterations> <filename>  Train the crew with rate limiting
  replay <task_id>        Replay from specific task
  help                    Show this help message

Rate Limiting Modes:
  Conservative (default): 5s delays, 8 retries, safer for standard API accounts
  Aggressive (fast):      3s delays, 6 retries, for premium API accounts

Examples:
  python -m limco.main test-basic          # Quick configuration check
  python -m limco.main test-safe           # Safe full test
  python -m limco.main run "Build a CRM for small business"
  python -m limco.main run-fast "Create a mobile app"
  python -m limco.main train 5 training_results.json

Troubleshooting:
  See docs/TROUBLESHOOTING_GUIDE.md for detailed help
            """)
        else:
            # Treat first argument as CEO goal
            run()
    else:
        # No arguments, run with default goal
        run()
