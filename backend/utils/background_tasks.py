"""
Background task utilities for running async operations without blocking HTTP requests.
"""
import asyncio
import logging
from typing import Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)


def run_in_background(func: Callable) -> Callable:
    """
    Decorator to run async functions in background without blocking.
    
    Usage:
        @run_in_background
        async def my_task(arg1, arg2):
            # Long-running task
            pass
        
        # Call it - returns immediately
        my_task(val1, val2)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Get or create event loop
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No running loop, create new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Schedule task in background
            task = loop.create_task(func(*args, **kwargs))
            
            # Add callback for error logging
            def log_exception(future):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Background task {func.__name__} failed: {e}", exc_info=True)
            
            task.add_done_callback(log_exception)
            
            logger.info(f"✓ Background task {func.__name__} started")
            
        except Exception as e:
            logger.error(f"Failed to start background task {func.__name__}: {e}", exc_info=True)
    
    return wrapper


async def run_async_task(coro):
    """
    Run an async coroutine in the background.
    
    Args:
        coro: Coroutine to run
        
    Returns:
        None (runs in background)
    """
    try:
        await coro
    except Exception as e:
        logger.error(f"Background async task failed: {e}", exc_info=True)


def schedule_background_task(coro):
    """
    Schedule a coroutine to run in the background without blocking.
    
    Args:
        coro: Coroutine to schedule
        
    Usage:
        schedule_background_task(analyze_profile(employee_id, db))
    """
    try:
        # Get or create event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Create task
        task = loop.create_task(run_async_task(coro))
        
        logger.info(f"✓ Background task scheduled")
        
    except Exception as e:
        logger.error(f"Failed to schedule background task: {e}", exc_info=True)
