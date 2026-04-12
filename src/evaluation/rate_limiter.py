import time
from threading import Lock
from src.observability.log_config import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Tracks API calls and enforces rate limits.
    Automatically waits when limit is approached.
    """

    def __init__(
        self,
        calls_per_minute: int = 30,
        buffer: int = 2
    ):
        """
        calls_per_minute : Groq free tier = 30 RPM
        buffer           : calls to keep in reserve
        """
        self.limit     = calls_per_minute - buffer  # safe limit = 28
        self.window    = 60.0                        # 1 minute window
        self.calls     = []                          # timestamps
        self.lock      = Lock()

    def wait_if_needed(self):
        """
        Call this before every API request.
        Automatically sleeps if rate limit is close.
        """
        with self.lock:
            now = time.time()

            # Remove calls older than 1 minute
            self.calls = [
                t for t in self.calls
                if now - t < self.window
            ]

            # If at limit — wait until oldest call expires
            if len(self.calls) >= self.limit:
                oldest   = self.calls[0]
                wait_for = self.window - (now - oldest) + 1
                if wait_for > 0:
                    logger.info(
                        "Rate limit reached — waiting %ds...",
                        round(wait_for)
                    )
                    time.sleep(wait_for)

            # Record this call
            self.calls.append(time.time())


# Groq free tier: 30 requests per minute
RATE_LIMITER = RateLimiter(calls_per_minute=30)