import threading
import time

from app.core.config import settings


class RateLimiter:
    """Limiter en memoria: max_attempts por ventana de window_seconds por key."""

    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self._max_attempts = max_attempts
        self._window_seconds = window_seconds
        self._attempts: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def attempt(self, key: str) -> tuple[bool, int]:
        """Registra un intento y devuelve (permitido, retry_after_segundos)."""
        now = time.monotonic()
        with self._lock:
            timestamps = [
                t for t in self._attempts.get(key, [])
                if now - t < self._window_seconds
            ]
            if len(timestamps) >= self._max_attempts:
                self._attempts[key] = timestamps
                retry_after = max(
                    0, int(self._window_seconds - (now - timestamps[0]))
                )
                return False, retry_after
            timestamps.append(now)
            self._attempts[key] = timestamps
            return True, 0

    def reset(self, key: str | None = None) -> None:
        with self._lock:
            if key is None:
                self._attempts.clear()
            else:
                self._attempts.pop(key, None)


login_rate_limiter = RateLimiter(
    max_attempts=settings.LOGIN_MAX_ATTEMPTS,
    window_seconds=settings.LOGIN_WINDOW_SECONDS,
)
