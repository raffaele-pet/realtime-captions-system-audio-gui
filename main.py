"""Graphical entry point for realtime-captions-system-audio."""

from __future__ import annotations

import sys
import ctypes
import socket
from pathlib import Path

_instance_guard = None


def _restore_missing_streams() -> None:
    """pythonw.exe sets stdout/stderr to None; some download libraries require them."""
    if sys.stdout is not None and sys.stderr is not None:
        return
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(exist_ok=True)
    stream = open(log_dir / "realtime-captions.log", "a", encoding="utf-8", buffering=1)
    if sys.stdout is None:
        sys.stdout = stream
    if sys.stderr is None:
        sys.stderr = stream


_restore_missing_streams()


def _focus_existing_window() -> None:
    """Bring the already-running application window to the foreground."""
    user32 = ctypes.windll.user32
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def visit(hwnd, _lparam):
        length = user32.GetWindowTextLengthW(hwnd)
        if length:
            title = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title, length + 1)
            if title.value == "Realtime Captions":
                user32.ShowWindow(hwnd, 9)
                user32.SetForegroundWindow(hwnd)
                return False
        return True

    user32.EnumWindows(callback_type(visit), 0)


def _acquire_single_instance() -> bool:
    global _instance_guard
    guard = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        guard.bind(("127.0.0.1", 47653))
        guard.listen(1)
    except OSError:
        guard.close()
        _focus_existing_window()
        return False
    _instance_guard = guard
    return True

if __name__ == "__main__":
    if _acquire_single_instance():
        from src.realtime_captions.gui import run_gui

        run_gui()
