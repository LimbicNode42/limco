"""
Rate-limited crew executio        else:
            # Default conservative settings for users with standard rate limits
            configure_rate_limiter(
                base_delay=5.0,      # Increased from 3.0
                max_delay=300.0,     # Increased to 5 minutes
                max_retries=8        # Increased from 6
            )er for Limco.
Provides intelligent rate limiting and retry logic for autonomous agent operations.
"""

import logging
from typing import Dict, Any, Optional
from crewai import Crew
from limco.utils.rate_limiter import add_task_delay, configure_rate_limiter

logger = logging.getLogger(__name__)

class RateLimitedCrew:
    """
    Wrapper for CrewAI crew that adds intelligent rate limiting and retry logic.
    """
    
    def __init__(self, crew: Crew, 
                 rate_limit_config: Optional[Dict[str, Any]] = None):
        """
        Initialize rate-limited crew wrapper.
        
        Args:
            crew: CrewAI crew instance
            rate_limit_config: Optional rate limiting configuration
        """
        self.crew = crew
        
        # Configure rate limiter with custom settings if provided
        if rate_limit_config:
            configure_rate_limiter(**rate_limit_config)
        else:
            # Default conservative settings for API rate limits
            configure_rate_limiter(
                base_delay=3.0,      # 3 second base delay
                max_delay=180.0,     # Max 3 minute delay
                max_retries=6        # Up to 6 retries
            )
    
    def kickoff(self, inputs: Dict[str, Any]) -> Any:
        """
        Execute crew with rate limiting and intelligent task delays.
        
        Args:
            inputs: Input parameters for the crew
            
        Returns:
            Crew execution result
        """
        logger.info("🚀 Starting rate-limited crew execution")
        logger.info(f"📋 Input goal: {inputs.get('ceo_goal', 'Unknown')[:100]}...")
        
        # Add initial delay to prevent immediate API hammering
        logger.info("⏸️ Initial startup delay...")
        import time
        time.sleep(2.0)
        
        try:
            # Execute crew with built-in retry logic
            result = self._execute_with_retry(inputs)
            
            logger.info("✅ Rate-limited crew execution completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ Rate-limited crew execution failed: {e}")
            # Re-raise with additional context
            raise Exception(f"Rate-limited execution failed: {e}")
    
    def _execute_with_retry(self, inputs: Dict[str, Any]) -> Any:
        """
        Execute crew with comprehensive retry logic.
        
        Args:
            inputs: Input parameters for the crew
            
        Returns:
            Crew execution result
        """
        max_attempts = 5  # Increased from 3 to handle rate limits better
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                if attempt > 0:
                    logger.warning(f"🔄 Crew execution retry {attempt}/{max_attempts-1}")
                    # Progressive delay between full crew retries (increased delays)
                    delay = 60.0 * attempt  # 60s, 120s, 180s, 240s delays
                    logger.info(f"⏸️ Waiting {delay}s before retry...")
                    import time
                    time.sleep(delay)
                
                # Execute the crew
                return self.crew.kickoff(inputs)
                
            except Exception as e:
                last_exception = e
                error_msg = str(e).lower()
                
                # Check if it's a rate limit related error
                if any(phrase in error_msg for phrase in [
                    'rate limit', 'too many requests', '429',
                    'quota exceeded', 'rate_limit_error', 'overloaded', '529'
                ]):
                    logger.warning(f"⚠️ Rate limit encountered in crew execution: {e}")
                    if attempt < max_attempts - 1:
                        continue
                
                # Check if it's a retryable connection error
                elif any(phrase in error_msg for phrase in [
                    'timeout', 'connection', 'server error', '500', '502', '503'
                ]):
                    logger.warning(f"⚠️ Connection error in crew execution: {e}")
                    if attempt < max_attempts - 1:
                        continue
                
                # Non-retryable error or final attempt
                logger.error(f"❌ Crew execution failed: {e}")
                break
        
        # All retries exhausted
        raise last_exception

    def train(self, n_iterations: int, filename: str, inputs: Dict[str, Any]) -> str:
        """
        Train crew with rate limiting between iterations.
        
        Args:
            n_iterations: Number of training iterations
            filename: Output filename for training results
            inputs: Input parameters for training
            
        Returns:
            Training results filename
        """
        logger.info(f"🎯 Starting rate-limited crew training: {n_iterations} iterations")
        
        try:
            # Add delay between training iterations to respect rate limits
            import time
            
            for i in range(n_iterations):
                if i > 0:
                    # Progressive delay between training iterations
                    delay = min(10.0 + (i * 2.0), 60.0)  # 10s + 2s per iteration, max 60s
                    logger.info(f"⏸️ Training iteration {i+1}/{n_iterations} - waiting {delay}s")
                    time.sleep(delay)
                
                logger.info(f"🔄 Training iteration {i+1}/{n_iterations}")
            
            # Execute training
            result = self.crew.train(n_iterations, filename, inputs)
            
            logger.info(f"✅ Rate-limited training completed: {filename}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Rate-limited training failed: {e}")
            raise Exception(f"Rate-limited training failed: {e}")


def create_rate_limited_crew(crew: Crew, 
                           aggressive_mode: bool = False) -> RateLimitedCrew:
    """
    Create a rate-limited crew wrapper with appropriate settings.
    
    Args:
        crew: CrewAI crew instance
        aggressive_mode: If True, use more aggressive (faster) rate limiting
        
    Returns:
        RateLimitedCrew instance
    """
    if aggressive_mode:
        # More aggressive settings for users with higher rate limits
        rate_config = {
            'base_delay': 3.0,      # Increased from 1.5 for better stability
            'max_delay': 120.0,     # Increased to 2 minutes
            'max_retries': 6        # Increased from 4
        }
        logger.info("⚡ Using aggressive rate limiting (faster, for higher API limits)")
    else:
        # Conservative settings for users with standard rate limits
        rate_config = {
            'base_delay': 5.0,      # Increased from 3.0
            'max_delay': 300.0,     # Increased to 5 minutes
            'max_retries': 8        # Increased from 6
        }
        logger.info("🐌 Using conservative rate limiting (safer for standard API limits)")
    
    return RateLimitedCrew(crew, rate_config)
