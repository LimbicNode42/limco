#!/usr/bin/env python
import sys
import warnings
import os
from datetime import datetime
from pathlib import Path
from limco.crew import Limco

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
        result = Limco().crew().kickoff(inputs=inputs)
        
        print("\n" + "="*80)
        print("✅ Autonomous development planning completed!")
        print("📄 Executive summary saved to: executive_summary.md")
        print("🎯 Ready for CEO review and approval")
        
        return result
        
    except Exception as e:
        print(f"❌ An error occurred while running the crew: {e}")
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
        Limco().crew().train(n_iterations=iterations, filename=filename, inputs=inputs)
        print(f"✅ Training completed for {iterations} iterations")
        
    except Exception as e:
        print(f"❌ An error occurred while training the crew: {e}")
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
        result = Limco().crew().kickoff(inputs=inputs)
        print("✅ Test completed successfully!")
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise Exception(f"An error occurred while testing the crew: {e}")


if __name__ == "__main__":
    """
    Command line interface for Limco Autonomous Software Development Company
    
    Commands:
    - run: Execute the full development planning process (default)
    - train <iterations> <filename>: Train the crew
    - replay <task_id>: Replay from a specific task
    - test: Test with a simple goal
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
        elif command == "run":
            # Remove command and use remaining as goal
            sys.argv = sys.argv[1:]
            run()
        else:
            # Treat first argument as CEO goal
            run()
    else:
        # No arguments, run with default goal
        run()
