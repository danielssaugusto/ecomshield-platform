from collections import defaultdict
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Request, status

class InMemoryRateLimiter:
    """In-memory sliding window rate limiter for protecting endpoints like authentication.
    
    Attributes:
        max_requests (int): Maximum allowed requests per window.
        window_seconds (int): Time window duration in seconds.
    """
    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history: dict[str, list[datetime]] = defaultdict(list)

    def reset(self) -> None:
        """Clear all rate limit history (useful for testing)."""
        self._history.clear()

    def __call__(self, request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        now = datetime.now(UTC)
        cutoff = now - timedelta(seconds=self.window_seconds)
        
        # Clean expired timestamps
        self._history[client_ip] = [ts for ts in self._history[client_ip] if ts > cutoff]
        
        if len(self._history[client_ip]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Limite de {self.max_requests} tentativas de autenticação por minuto excedido. Tente novamente em {self.window_seconds} segundos.",
                headers={"Retry-After": str(self.window_seconds)},
            )
        
        self._history[client_ip].append(now)

# Global instance for auth token endpoint (5 requests per 60s)
auth_rate_limiter = InMemoryRateLimiter(max_requests=5, window_seconds=60)
