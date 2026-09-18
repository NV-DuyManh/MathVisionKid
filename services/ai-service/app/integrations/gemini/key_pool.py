"""
Safe Key Pool for Google Gemini API credentials.
Enforces single comma-separated variable, credential masking, state tracking, and quota respect.
"""

import time
import logging
from enum import Enum
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)


class GeminiKeyState(str, Enum):
    HEALTHY = "HEALTHY"
    COOLING_DOWN = "COOLING_DOWN"
    DISABLED_AUTH = "DISABLED_AUTH"
    DEGRADED = "DEGRADED"


class GeminiKeyEntry:
    def __init__(self, raw_key: str, index: int):
        self.raw_key = raw_key
        self.index = index
        self.state = GeminiKeyState.HEALTHY
        self.cooldown_until: float = 0.0
        self.failure_count: int = 0
        self.total_calls: int = 0
        self.last_used_at: float = 0.0

        # Safe ID: one-way SHA256 fingerprint, never reveals any raw key content
        import hashlib
        h = hashlib.sha256(raw_key.encode()).hexdigest()[:16]
        self.safe_id = f"sha256:{h}"

    def is_available(self) -> bool:
        if self.state == GeminiKeyState.DISABLED_AUTH:
            return False
        if self.state == GeminiKeyState.COOLING_DOWN:
            return time.time() >= self.cooldown_until
        return True


class GeminiKeyPool:
    def __init__(
        self,
        raw_keys_str: str = "",
        cooldown_seconds: float = 60.0,
        rotate_on_429: bool = False,
    ):
        self.cooldown_seconds = cooldown_seconds
        self.rotate_on_429 = rotate_on_429
        self.entries: List[GeminiKeyEntry] = []
        self._current_index = 0
        self._parse_and_init(raw_keys_str)

    def _parse_and_init(self, raw_keys_str: str):
        if not raw_keys_str or not isinstance(raw_keys_str, str):
            self.entries = []
            return

        # Split comma, trim whitespace, discard blanks, dedup preserving order
        seen = set()
        deduped = []
        for part in raw_keys_str.split(","):
            cleaned = part.strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                deduped.append(cleaned)

        self.entries = [GeminiKeyEntry(k, idx) for idx, k in enumerate(deduped)]
        logger.info(f"[GeminiKeyPool] Initialized with {len(self.entries)} keys")

    @property
    def total_keys(self) -> int:
        return len(self.entries)

    @property
    def active_keys(self) -> int:
        return sum(1 for e in self.entries if e.is_available())

    def lease_key(self) -> Optional[GeminiKeyEntry]:
        if not self.entries:
            return None

        now = time.time()
        # Recover expired cooldowns
        for e in self.entries:
            if e.state == GeminiKeyState.COOLING_DOWN and now >= e.cooldown_until:
                e.state = GeminiKeyState.HEALTHY
                e.failure_count = 0

        # Round-robin or first available
        n = len(self.entries)
        for i in range(n):
            idx = (self._current_index + i) % n
            entry = self.entries[idx]
            if entry.is_available():
                self._current_index = (idx + 1) % n
                entry.last_used_at = now
                entry.total_calls += 1
                return entry

        return None

    def mark_success(self, entry: GeminiKeyEntry):
        if entry.state != GeminiKeyState.DISABLED_AUTH:
            entry.state = GeminiKeyState.HEALTHY
            entry.failure_count = 0

    def mark_failure(self, entry: GeminiKeyEntry, error_type: str, retry_after: Optional[float] = None):
        now = time.time()
        entry.failure_count += 1

        if error_type in ("AUTH_ERROR", "401", "403"):
            entry.state = GeminiKeyState.DISABLED_AUTH
            logger.warning(f"[GeminiKeyPool] Key {entry.safe_id} DISABLED_AUTH due to {error_type}")
        elif error_type in ("RATE_LIMIT_429", "429"):
            if not self.rotate_on_429:
                # Quota backoff on this key without aggressive sweeping
                cooldown = retry_after if (retry_after and retry_after > 0) else self.cooldown_seconds
                entry.state = GeminiKeyState.COOLING_DOWN
                entry.cooldown_until = now + cooldown
                logger.warning(f"[GeminiKeyPool] Key {entry.safe_id} 429 backoff for {cooldown:.1f}s (no sweep)")
            else:
                entry.state = GeminiKeyState.COOLING_DOWN
                entry.cooldown_until = now + (retry_after or self.cooldown_seconds)
        else:
            # 5xx or transient timeout
            entry.state = GeminiKeyState.COOLING_DOWN
            entry.cooldown_until = now + self.cooldown_seconds
            logger.warning(f"[GeminiKeyPool] Key {entry.safe_id} transient error {error_type}, cooling down")


# Module-level singleton
_gemini_pool: Optional[GeminiKeyPool] = None


def init_gemini_pool(raw_keys_str: str = "", rotate_on_429: bool = False) -> GeminiKeyPool:
    global _gemini_pool
    _gemini_pool = GeminiKeyPool(raw_keys_str=raw_keys_str, rotate_on_429=rotate_on_429)
    return _gemini_pool


def get_gemini_pool() -> Optional[GeminiKeyPool]:
    return _gemini_pool
