"""
Rate limiting utilities for Limco autonomous development company.
Handles API rate limits with exponential backoff and intelligent delays.
"""

import time
import random
from typing import Optional, Callable, Any
from functools import wraps
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Intelligent rate limiter with exponential backoff for AI API calls.
    """
    
    def __init__(self, 
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 max_retries: int = 5,
                 backoff_factor: float = 2.0):
        """
        Initialize rate limiter.
        
        Args:
            base_delay: Base delay between operations (seconds)
            max_delay: Maximum delay between retries (seconds)
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for exponential backoff
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.last_request_time = 0.0

    def wait_if_needed(self):
        """Add intelligent delay between operations."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.base_delay:
            delay = self.base_delay - time_since_last
            # Add small random jitter to prevent thundering herd
            jitter = random.uniform(0.1, 0.3)
            total_delay = delay + jitter
            
            logger.info(f"⏱️ Rate limiting: waiting {total_delay:.2f}s")
            time.sleep(total_delay)
        
        self.last_request_time = time.time()

    def retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with exponential backoff retry logic.
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries are exhausted
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    # Calculate delay with exponential backoff
                    delay = min(
                        self.base_delay * (self.backoff_factor ** (attempt - 1)),
                        self.max_delay
                    )
                    # Add jitter to prevent synchronized retries
                    jitter = random.uniform(0.8, 1.2)
                    total_delay = delay * jitter
                    
                    logger.warning(f"🔄 Retry attempt {attempt}/{self.max_retries} "
                                 f"after {total_delay:.2f}s delay")
                    time.sleep(total_delay)
                
                # Wait for rate limiting before executing
                self.wait_if_needed()
                
                # Execute function
                result = func(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"✅ Success after {attempt} retries")
                
                return result
                
            except Exception as e:
                last_exception = e
                error_msg = str(e).lower()
                
                # Check if it's a rate limit error
                if any(phrase in error_msg for phrase in [
                    'rate limit', 'too many requests', '429', 
                    'quota exceeded', 'rate_limit_error', 'overloaded', '529'
                ]):
                    logger.warning(f"⚠️ Rate limit hit: {e}")
                    if attempt == self.max_retries:
                        logger.error(f"❌ Max retries exhausted for rate limiting")
                        break
                    continue
                
                # Check if it's a retryable error
                elif any(phrase in error_msg for phrase in [
                    'timeout', 'connection', 'server error', '500', '502', '503'
                ]):
                    logger.warning(f"⚠️ Retryable error: {e}")
                    if attempt == self.max_retries:
                        logger.error(f"❌ Max retries exhausted for connection error")
                        break
                    continue
                
                # Non-retryable error
                else:
                    logger.error(f"❌ Non-retryable error: {e}")
                    raise e
        
        # All retries exhausted
        raise last_exception


# Global rate limiter instance
_global_rate_limiter = RateLimiter(
    base_delay=2.0,      # 2 second base delay between operations
    max_delay=120.0,     # Max 2 minute delay
    max_retries=5,       # Up to 5 retries
    backoff_factor=2.0   # Double delay each retry
)


def rate_limited(func: Callable) -> Callable:
    """
    Decorator to add rate limiting and retry logic to functions.
    
    Usage:
        @rate_limited
        def api_call():
            # Your API call here
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return _global_rate_limiter.retry_with_backoff(func, *args, **kwargs)
    
    return wrapper


def add_task_delay(phase_number: int, task_number: int, total_tasks: int):
    """
    Add intelligent delays between tasks based on phase and complexity.
    
    Args:
        phase_number: Current phase (1-5)
        task_number: Current task number in phase
        total_tasks: Total number of tasks in phase
    """
    # Base delay increases with phase complexity
    base_delays = {
        1: 1.0,   # Goal intake - lighter processing
        2: 2.0,   # Technical planning - medium complexity
        3: 1.5,   # Business analysis - medium complexity
        4: 1.0,   # Quality planning - lighter processing
        5: 2.5    # Implementation - heavy processing
    }
    
    base_delay = base_delays.get(phase_number, 1.5)
    
    # Add jitter to prevent synchronized requests
    jitter = random.uniform(0.8, 1.2)
    delay = base_delay * jitter
    
    logger.info(f"⏸️ Phase {phase_number} task delay: {delay:.2f}s")
    time.sleep(delay)


def configure_rate_limiter(base_delay: float = 2.0, 
                          max_delay: float = 120.0,
                          max_retries: int = 5):
    """
    Configure global rate limiter settings.
    
    Args:
        base_delay: Base delay between operations (seconds)
        max_delay: Maximum delay between retries (seconds) 
        max_retries: Maximum number of retry attempts
    """
    global _global_rate_limiter
    _global_rate_limiter = RateLimiter(
        base_delay=base_delay,
        max_delay=max_delay,
        max_retries=max_retries
    )
    
    logger.info(f"🔧 Rate limiter configured: {base_delay}s base, "
                f"{max_delay}s max, {max_retries} retries")
