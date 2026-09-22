"""Shared mutable state for the realtime captions pipeline.

All public functions acquire the module-level lock internally so callers
never need to manage synchronisation themselves.
"""

import threading
from collections import deque
from dataclasses import dataclass


# ── lock ──────────────────────────────────────────────────────────────────────
_lock = threading.Lock()


# ── text state ────────────────────────────────────────────────────────────────
_live_text: str   = ""
_stable_text: str = ""
_status: str      = "Initializing"
_history: deque[tuple[str, str]] = deque(maxlen=100)
MAX_LIVE_CHARS = 12_000


# ── resource snapshot ─────────────────────────────────────────────────────────
@dataclass
class Resources:
    cpu_pct: float          = 0.0
    ram_used_gb: float      = 0.0
    ram_total_gb: float     = 0.0
    ram_pct: float          = 0.0
    gpu_name: str           = ""
    gpu_pct: float | None          = None
    gpu_mem_used_gb: float | None  = None
    gpu_mem_total_gb: float | None = None
    gpu_mem_pct: float | None      = None
    gpu_temp: float | None         = None


_res = Resources()


# ── setters ───────────────────────────────────────────────────────────────────
def set_live_text(text: str) -> None:
    global _live_text
    with _lock:
        # Keep only the display-relevant tail during abnormally long utterances.
        _live_text = text.strip()[-MAX_LIVE_CHARS:]


def set_stable_text(text: str) -> None:
    global _stable_text
    with _lock:
        _stable_text = text.strip()[-MAX_LIVE_CHARS:]


def set_status(status: str) -> None:
    global _status
    with _lock:
        _status = status


def append_history(timestamp: str, text: str) -> None:
    with _lock:
        _history.append((timestamp, text))


def clear_live(*, clear_stable: bool = True) -> None:
    """Clear in-progress text after a final utterance is committed."""
    global _live_text, _stable_text
    with _lock:
        _live_text = ""
        if clear_stable:
            _stable_text = ""


def reset_history(maxlen: int = 100) -> None:
    global _history
    with _lock:
        _history = deque(maxlen=maxlen)


def update_resources(**kwargs: object) -> None:
    """Batch-update resource fields under a single lock acquisition."""
    with _lock:
        for key, value in kwargs.items():
            setattr(_res, key, value)


# ── getters ───────────────────────────────────────────────────────────────────
def get_snapshot() -> tuple[str, str, str, list[tuple[str, str]], Resources]:
    """Return a consistent copy of all UI-relevant state."""
    with _lock:
        return (
            _live_text,
            _stable_text,
            _status,
            list(_history),
            Resources(**_res.__dict__),
        )


def get_resources_snapshot() -> Resources:
    with _lock:
        return Resources(**_res.__dict__)
