"""Borderless always-on-top caption overlay window.

Runs Tkinter's mainloop in its own daemon thread.
Mouse clicks pass through to applications below via WS_EX_TRANSPARENT.

Currently Windows-only for click-through behaviour; the window still renders
on other platforms but will not be click-through.
"""

import ctypes
import threading
import tkinter as tk


class CaptionOverlay(threading.Thread):
    BG         = "#0e0e0e"
    FG         = "#ffff00"
    FONT       = ("Arial", 24, "bold")
    ALPHA      = 0.88
    MIN_HEIGHT = 72    # enough for one line + padding
    MAX_HEIGHT = 210   # cap at ~3 lines — beyond this the overlay is too intrusive

    def __init__(self) -> None:
        super().__init__(daemon=True, name="caption-overlay")
        self._text             = ""
        self._lock             = threading.Lock()
        self._root: tk.Tk | None = None
        self._sw: int = 0
        self._sh: int = 0
        self._width: int = 0

    def set_text(self, text: str) -> None:
        with self._lock:
            self._text = text

    def stop(self) -> None:
        if self._root is not None:
            try:
                self._root.after(0, self._root.destroy)
            except Exception:
                pass

    def run(self) -> None:
        root = tk.Tk()
        self._root = root

        root.title("")
        root.overrideredirect(True)
        root.wm_attributes("-toolwindow", True)
        root.attributes("-topmost", True)
        root.configure(bg=self.BG)

        # Start fully transparent — alpha controls visibility instead of
        # withdraw/deiconify, which is unreliable with overrideredirect on Windows.
        root.attributes("-alpha", 0.0)

        root.update_idletasks()

        self._sw    = root.winfo_screenwidth()
        self._sh    = root.winfo_screenheight()
        self._width = min(int(self._sw * 0.72), 1280)
        x           = (self._sw - self._width) // 2
        y           = self._sh - self.MIN_HEIGHT - 72

        root.geometry(f"{self._width}x{self.MIN_HEIGHT}+{x}+{y}")

        self._label = tk.Label(
            root,
            text="",
            font=self.FONT,
            fg=self.FG,
            bg=self.BG,
            wraplength=self._width - 56,
            justify="center",
            padx=28,
            pady=14,
        )
        self._label.pack(fill="both", expand=True)

        # Defer click-through setup until after the window is fully mapped
        root.after(200, lambda: self._set_click_through(root))
        root.after(80, self._poll)
        root.mainloop()

    @staticmethod
    def _set_click_through(root: tk.Tk) -> None:
        """Apply WS_EX_TRANSPARENT to the real top-level HWND.

        winfo_id() returns the inner child frame on Windows, so we walk up
        via GetAncestor(GA_ROOT=2) to target the actual top-level window.
        """
        try:
            GA_ROOT           = 2
            GWL_EXSTYLE       = -20
            WS_EX_TRANSPARENT = 0x00000020
            child_hwnd = root.winfo_id()
            hwnd       = ctypes.windll.user32.GetAncestor(child_hwnd, GA_ROOT)
            cur        = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, cur | WS_EX_TRANSPARENT)
        except Exception:
            pass

    def _poll(self) -> None:
        if self._root is None:
            return
        with self._lock:
            text = self._text
        if text:
            self._label.config(text=text)
            self._resize_to_fit()
            if self._root.attributes("-alpha") == 0.0:
                self._root.attributes("-alpha", self.ALPHA)
                self._root.lift()
        else:
            if self._root.attributes("-alpha") != 0.0:
                self._root.attributes("-alpha", 0.0)
        self._root.after(80, self._poll)

    def _resize_to_fit(self) -> None:
        """Grow the window upward to fit the label's content, capped at MAX_HEIGHT."""
        self._root.update_idletasks()  # type: ignore[union-attr]
        needed = self._label.winfo_reqheight()
        height = max(self.MIN_HEIGHT, min(needed, self.MAX_HEIGHT))
        y      = self._sh - height - 72
        self._root.geometry(f"{self._width}x{height}+{(self._sw - self._width) // 2}+{y}")  # type: ignore[union-attr]
