"""Model configuration with rate limiting and fallback strategies.

Implements differentiated model selection for technical vs non-technical agents:
- Technical agents: claude-4-sonnet-latest with gemini-2.5-flash, claude-3-7-sonnet-latest fallbacks
- Non-technical agents: gemini-2.5-flash with gemini-2.0-flash, claude-3-7-sonnet-latest fallbacks

Includes built-in rate limiting for API tier compliance.
"""

import os
from typing import Dict, List, Any
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_core.language_models import BaseChatModel

# Load environment variables
load_dotenv()


# Rate limiter configurations optimized for actual API tier limits
def create_conservative_rate_limiter():
    """Conservative rate limiter optimized for 1000 RPM limits (50% utilization)."""
    return InMemoryRateLimiter(
        requests_per_second=8.3,  # ~500 RPM (50% of 1000 RPM limit)
        check_every_n_seconds=0.1,  # Check every 100ms
        max_bucket_size=25,  # Allow moderate bursts
    )

def create_moderate_rate_limiter():
    """Moderate rate limiter for balanced usage (70% utilization)."""
    return InMemoryRateLimiter(
        requests_per_second=11.7,  # ~700 RPM (70% of 1000 RPM limit)
        check_every_n_seconds=0.1,
        max_bucket_size=35,
    )

def create_relaxed_rate_limiter():
    """Aggressive rate limiter for high throughput (85% utilization)."""
    return InMemoryRateLimiter(
        requests_per_second=14.2,  # ~850 RPM (85% of 1000 RPM limit)
        check_every_n_seconds=0.1,
        max_bucket_size=45,
    )

def create_gemini_pro_rate_limiter():
    """Special rate limiter for Gemini Pro (150 RPM limit)."""
    return InMemoryRateLimiter(
        requests_per_second=2.0,   # ~120 RPM (80% of 150 RPM limit)
        check_every_n_seconds=0.1,
        max_bucket_size=10,
    )


# Technical agent classification
TECHNICAL_AGENTS = {
    "senior_engineer",
    "senior_engineer_aggregator", 
    "qa_engineer",
    "unit_test_evaluator",
    "self_review_evaluator",
    "peer_review_evaluator",
    "integration_test_evaluator"
}

NON_TECHNICAL_AGENTS = {
    "human_goal_setting",
    "cto",
    "engineering_manager", 
    "manager_review_evaluator",
    "cto_review_evaluator",
    "human_escalation_evaluator",
    "review"
}


def create_technical_model_chain() -> BaseChatModel:
    """Create model chain for technical agents with fallbacks."""
    
    # Primary model: Claude 4 Sonnet (best for technical work)
    primary_model = init_chat_model(
        "anthropic:claude-4-sonnet-latest",
        temperature=0.1,  # Low temperature for technical precision
        max_tokens=4096,
        rate_limiter=create_conservative_rate_limiter()
    )
    
    # Fallback 1: Gemini 2.5 Flash (good technical capability, faster)
    fallback_1 = init_chat_model(
        "google_genai:gemini-2.5-flash",
        temperature=0.1,
        max_tokens=4096,
        rate_limiter=create_moderate_rate_limiter()
    )
    
    # Fallback 2: Claude 3.7 Sonnet (reliable technical backup)
    fallback_2 = init_chat_model(
        "anthropic:claude-3-7-sonnet-latest",
        temperature=0.1,
        max_tokens=4096,
        rate_limiter=create_conservative_rate_limiter()
    )
    
    # Chain with fallbacks
    return primary_model.with_fallbacks([fallback_1, fallback_2])


def create_non_technical_model_chain() -> BaseChatModel:
    """Create model chain for non-technical agents with fallbacks."""
    
    # Primary model: Gemini 2.5 Flash (excellent for coordination/management)
    primary_model = init_chat_model(
        "google_genai:gemini-2.5-flash",
        temperature=0.3,  # Slightly higher temperature for creativity
        max_tokens=4096,
        rate_limiter=create_moderate_rate_limiter()
    )
    
    # Fallback 1: Gemini 2.0 Flash (faster, good for simple tasks)
    fallback_1 = init_chat_model(
        "google_genai:gemini-2.0-flash",
        temperature=0.3,
        max_tokens=4096,
        rate_limiter=create_relaxed_rate_limiter()
    )
    
    # Fallback 2: Claude 3.7 Sonnet (reliable backup)
    fallback_2 = init_chat_model(
        "anthropic:claude-3-7-sonnet-latest",
        temperature=0.3,
        max_tokens=4096,
        rate_limiter=create_conservative_rate_limiter()
    )
    
    # Chain with fallbacks
    return primary_model.with_fallbacks([fallback_1, fallback_2])


def get_model_for_agent(agent_name: str) -> BaseChatModel:
    """Get the appropriate model configuration for a specific agent.
    
    Args:
        agent_name: Name of the agent (e.g., 'senior_engineer', 'cto')
        
    Returns:
        Configured model with rate limiting and fallbacks
    """
    
    if agent_name in TECHNICAL_AGENTS:
        print(f"🔧 Using technical model chain for {agent_name}")
        return create_technical_model_chain()
    elif agent_name in NON_TECHNICAL_AGENTS:
        print(f"📊 Using non-technical model chain for {agent_name}")
        return create_non_technical_model_chain()
    else:
        # Default to non-technical for unknown agents
        print(f"❓ Unknown agent {agent_name}, defaulting to non-technical model chain")
        return create_non_technical_model_chain()


def get_model_info() -> Dict[str, Any]:
    """Get information about model configurations."""
    return {
        "technical_agents": {
            "agents": list(TECHNICAL_AGENTS),
            "primary_model": "anthropic:claude-4-sonnet-latest",
            "fallbacks": ["google_genai:gemini-2.5-flash", "anthropic:claude-3-7-sonnet-latest"],
            "temperature": 0.1,
            "use_case": "Technical development, coding, testing, reviews"
        },
        "non_technical_agents": {
            "agents": list(NON_TECHNICAL_AGENTS),  
            "primary_model": "google_genai:gemini-2.5-flash",
            "fallbacks": ["google_genai:gemini-2.0-flash", "anthropic:claude-3-7-sonnet-latest"],
            "temperature": 0.3,
            "use_case": "Management, coordination, planning, reviews"
        },
        "rate_limiting": {
            "conservative": "8.3 req/sec (~500 RPM), 25 burst - 50% of API limits",
            "moderate": "11.7 req/sec (~700 RPM), 35 burst - 70% of API limits", 
            "relaxed": "14.2 req/sec (~850 RPM), 45 burst - 85% of API limits",
            "gemini_pro": "2 req/sec (~120 RPM), 10 burst - For 150 RPM limited models"
        }
    }


def validate_api_keys() -> Dict[str, bool]:
    """Validate that required API keys are available."""
    required_keys = {
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
        "LANGSMITH_API_KEY": os.getenv("LANGSMITH_API_KEY")
    }
    
    validation_results = {}
    for key, value in required_keys.items():
        validation_results[key] = value is not None and len(value.strip()) > 0
        
    return validation_results


if __name__ == "__main__":
    # Test the model configuration
    print("Model Configuration Test")
    print("=" * 50)
    
    # Validate API keys
    print("\n🔑 API Key Validation:")
    key_status = validate_api_keys()
    for key, is_valid in key_status.items():
        status = "✅" if is_valid else "❌"
        print(f"  {status} {key}: {'Valid' if is_valid else 'Missing or empty'}")
    
    # Show model info
    print("\n📋 Model Configuration:")
    model_info = get_model_info()
    
    print(f"\n🔧 Technical Agents ({len(model_info['technical_agents']['agents'])}):")
    print(f"  Primary: {model_info['technical_agents']['primary_model']}")
    print(f"  Fallbacks: {', '.join(model_info['technical_agents']['fallbacks'])}")
    print(f"  Temperature: {model_info['technical_agents']['temperature']}")
    print(f"  Agents: {', '.join(model_info['technical_agents']['agents'])}")
    
    print(f"\n📊 Non-Technical Agents ({len(model_info['non_technical_agents']['agents'])}):")
    print(f"  Primary: {model_info['non_technical_agents']['primary_model']}")
    print(f"  Fallbacks: {', '.join(model_info['non_technical_agents']['fallbacks'])}")
    print(f"  Temperature: {model_info['non_technical_agents']['temperature']}")
    print(f"  Agents: {', '.join(model_info['non_technical_agents']['agents'])}")
    
    print(f"\n⏱️ Rate Limiting:")
    for tier, limit in model_info['rate_limiting'].items():
        print(f"  {tier.title()}: {limit}")
