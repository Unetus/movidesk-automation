"""Rate limiter for API requests."""

import time
from collections import deque
from threading import Lock
from typing import Optional


class RateLimiter:
    """
    Token bucket rate limiter.
    
    Ensures requests don't exceed specified rate limit.
    """
    
    def __init__(self, max_requests: int, time_window: int):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: deque = deque()
        self.lock = Lock()
    
    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Acquire permission to make a request.
        
        Args:
            blocking: If True, wait until permission is granted
            timeout: Maximum time to wait (None = wait forever)
        
        Returns:
            True if permission granted, False otherwise
        """
        start_time = time.time()
        
        while True:
            with self.lock:
                now = time.time()
                
                # Remove old requests outside time window
                while self.requests and self.requests[0] < now - self.time_window:
                    self.requests.popleft()
                
                # Check if we can make a request
                if len(self.requests) < self.max_requests:
                    self.requests.append(now)
                    return True
            
            # If non-blocking, return immediately
            if not blocking:
                return False
            
            # Check timeout
            if timeout is not None and (time.time() - start_time) >= timeout:
                return False
            
            # Wait a bit before retrying
            time.sleep(0.1)
    
    def get_wait_time(self) -> float:
        """
        Get estimated wait time before next request can be made.
        
        Returns:
            Wait time in seconds (0 if can make request now)
        """
        with self.lock:
            now = time.time()
            
            # Remove old requests
            while self.requests and self.requests[0] < now - self.time_window:
                self.requests.popleft()
            
            # If under limit, no wait needed
            if len(self.requests) < self.max_requests:
                return 0.0
            
            # Calculate when oldest request will expire
            oldest = self.requests[0]
            wait = (oldest + self.time_window) - now
            return max(0.0, wait)
