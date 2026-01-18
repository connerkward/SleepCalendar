"""Rate limiting middleware for API."""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import time
from collections import defaultdict
from typing import Dict, Tuple


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Max requests per minute per IP
            requests_per_hour: Max requests per hour per IP
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.minute_requests: Dict[str, list] = defaultdict(list)
        self.hour_requests: Dict[str, list] = defaultdict(list)
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier (IP address)."""
        # Get IP from forwarded header if behind proxy (Cloud Run)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def check_rate_limit(self, request: Request) -> Tuple[bool, str]:
        """
        Check if request is within rate limits.
        
        Returns:
            (allowed, error_message)
        """
        client_id = self._get_client_id(request)
        now = time.time()
        
        # Clean old entries (older than 1 hour)
        cutoff_hour = now - 3600
        cutoff_minute = now - 60
        
        # Clean minute requests
        self.minute_requests[client_id] = [
            ts for ts in self.minute_requests[client_id] if ts > cutoff_minute
        ]
        
        # Clean hour requests
        self.hour_requests[client_id] = [
            ts for ts in self.hour_requests[client_id] if ts > cutoff_hour
        ]
        
        # Check minute limit
        if len(self.minute_requests[client_id]) >= self.requests_per_minute:
            return False, f"Rate limit exceeded: {self.requests_per_minute} requests per minute"
        
        # Check hour limit
        if len(self.hour_requests[client_id]) >= self.requests_per_hour:
            return False, f"Rate limit exceeded: {self.requests_per_hour} requests per hour"
        
        # Record request
        self.minute_requests[client_id].append(now)
        self.hour_requests[client_id].append(now)
        
        return True, ""


# Global rate limiter instance
rate_limiter = RateLimiter(
    requests_per_minute=30,  # 30 requests per minute
    requests_per_hour=500     # 500 requests per hour
)
