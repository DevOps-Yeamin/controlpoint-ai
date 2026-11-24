import time
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import threading

class RateLimiter:
    """In-memory sliding window rate limiter and progressive throttling per agent identity."""
    def __init__(self):
        self._lock = threading.Lock()
        # agent_id -> list of timestamps
        self._timestamps: Dict[str, List[float]] = defaultdict(list)
        # agent_id -> list of unauthorized violation timestamps
        self._violations: Dict[str, List[float]] = defaultdict(list)

    def check_limit(
        self,
        agent_id: str,
        max_requests: int = 15,
        window_seconds: int = 60
    ) -> Tuple[bool, int, float]:
        """
        Check if request is allowed under standard sliding-window rate limits.
        
        Returns:
            Tuple of:
            - is_allowed (bool)
            - remaining_requests (int)
            - reset_in_seconds (float)
        """
        with self._lock:
            now = time.time()
            cutoff = now - window_seconds
            
            # Prune old timestamps
            self._timestamps[agent_id] = [t for t in self._timestamps[agent_id] if t > cutoff]
            current_count = len(self._timestamps[agent_id])

            if current_count >= max_requests:
                oldest = self._timestamps[agent_id][0]
                retry_after = max(0.1, (oldest + window_seconds) - now)
                return False, 0, retry_after

            # Register current request
            self._timestamps[agent_id].append(now)
            remaining = max(0, max_requests - (current_count + 1))
            return True, remaining, 0.0

    def record_violation(
        self,
        agent_id: str,
        threshold: int = 3,
        window_seconds: int = 60
    ) -> Tuple[bool, float]:
        """
        Record an unauthorized/denied security violation.
        If consecutive violations reach threshold within window, triggers progressive throttle.
        Returns: (is_throttled, retry_after_seconds)
        """
        with self._lock:
            now = time.time()
            cutoff = now - window_seconds
            self._violations[agent_id] = [t for t in self._violations[agent_id] if t > cutoff]
            self._violations[agent_id].append(now)

            if len(self._violations[agent_id]) >= threshold:
                oldest = self._violations[agent_id][0]
                retry_after = max(0.1, (oldest + window_seconds) - now)
                return True, retry_after
            return False, 0.0

    def is_violation_locked(self, agent_id: str, threshold: int = 3, window_seconds: int = 60) -> Tuple[bool, float]:
        """Check if agent is currently locked out due to repeated violations."""
        with self._lock:
            now = time.time()
            cutoff = now - window_seconds
            self._violations[agent_id] = [t for t in self._violations[agent_id] if t > cutoff]
            if len(self._violations[agent_id]) >= threshold:
                oldest = self._violations[agent_id][0]
                retry_after = max(0.1, (oldest + window_seconds) - now)
                return True, retry_after
            return False, 0.0

    def reset(self, agent_id: str = None):
        """Reset limits and violations for testing."""
        with self._lock:
            if agent_id:
                self._timestamps.pop(agent_id, None)
                self._violations.pop(agent_id, None)
            else:
                self._timestamps.clear()
                self._violations.clear()

# Global singleton
rate_limiter = RateLimiter()
