# Caption Overlay

The caption overlay is an optional floating subtitle window that renders on top of every other application — including video calls, browsers, and fullscreen apps — exactly like movie subtitles.

---

## What it looks like

```
┌─────────────────────────────────────────────────────────────────────┐  ← no title bar
│                                                                     │  ← dark bg, 88% opacity
│   And one experience, he actually played Hemi-Sync sounds into     │  ← white bold Arial 24
│   my ears while I was having the experience…                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                         [ Windows taskbar ]
```

**Position:** horizontally centred, 72 px above the taskbar.  
**Width:** 72 % of screen width, capped at 1280 px.  
**Height:** fixed at 130 px (accommodates ~2 lines of text with padding).

---

## Behaviour

| Behaviour | Detail |
|---|---|
| **Always on top** | `root.attributes("-topmost", True)` — floats above every window |
| **Click-through** | `WS_EX_TRANSPARENT` — mouse clicks reach the app below |
| **Hides when silent** | `alpha=0.0` when no text; `alpha=0.88` when text is present |
| **Not in taskbar** | `-toolwindow` hides it from the taskbar and Alt+Tab |
| **No window border** | `overrideredirect(True)` removes title bar and frame |
| **Updates at ~12 fps** | `root.after(80, _poll)` polls the shared text buffer every 80 ms |

---

## Text shown

The overlay displays `_stable_text` (stabilised Whisper output) when available, falling back to `_live_text` (raw partial). This mirrors the **Live** panel in the terminal UI.

When `recorder.text()` returns a final utterance, both `_stable_text` and `_live_text` are cleared — the overlay hides automatically until the next sentence begins.

---

## Windows API details

### Why `GetAncestor` instead of `winfo_id`?

`root.winfo_id()` returns the HWND of Tkinter's **inner child frame**, not the actual top-level window. Applying `WS_EX_LAYERED` to a child window is unsupported on Windows and breaks rendering. `GetAncestor(hwnd, GA_ROOT=2)` walks up the parent chain to the real top-level HWND.

```python
GA_ROOT    = 2
child_hwnd = root.winfo_id()
hwnd       = ctypes.windll.user32.GetAncestor(child_hwnd, GA_ROOT)
```

### Why not use `WS_EX_LAYERED`?

Tkinter sets `WS_EX_LAYERED` internally when you call `root.attributes("-alpha", value)`. Adding it again would be redundant. We only need to OR in `WS_EX_TRANSPARENT` to enable click-through.

```python
GWL_EXSTYLE       = -20
WS_EX_TRANSPARENT = 0x00000020
cur  = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, cur | WS_EX_TRANSPARENT)
```

### Why alpha=0 instead of `withdraw/deiconify`?

`overrideredirect(True)` (borderless mode) bypasses the Windows window manager message chain. As a side-effect, `root.withdraw()` + `root.deiconify()` does not reliably re-show the window on Windows — `deiconify()` silently fails.

**Solution:** The window is kept open at all times. Visibility is controlled by toggling between `alpha=0.0` (invisible) and `alpha=0.88` (visible). This is reliable across all Windows versions.

### Why defer `_set_click_through` by 200 ms?

The click-through style must be applied after the window's HWND is fully registered with Windows. Calling it synchronously during `run()` (before `mainloop()`) can target a window that hasn't been mapped yet, causing the style to be discarded. `root.after(200, ...)` schedules the call inside the Tkinter event loop after the window is fully initialised.

---

## `CaptionOverlay` class reference

```python
class CaptionOverlay(threading.Thread):
```

Runs in its own daemon thread. All public methods are thread-safe.

| Method | Description |
|---|---|
| `start()` | Inherited from `Thread`. Starts the Tkinter event loop. |
| `set_text(text: str)` | Update the displayed caption. Pass `""` to hide. |
| `stop()` | Schedule `root.destroy()` from outside the Tkinter thread. |

### Constants

| Constant | Default | Description |
|---|---|---|
| `BG` | `"#0e0e0e"` | Window background colour |
| `FG` | `"#ffffff"` | Text colour |
| `FONT` | `("Arial", 24, "bold")` | Caption font |
| `ALPHA` | `0.88` | Window opacity when visible |
| `HEIGHT` | `130` | Fixed window height in pixels |

---

## Known limitations

| Limitation | Reason |
|---|---|
| NVIDIA only for GPU stats | NVML (pynvml) only supports NVIDIA GPUs |
| Windows only for click-through | `ctypes.windll` is Windows-specific; the overlay still appears on other platforms but is not click-through |
| Taskbar always-on-top apps | Some apps (e.g., certain docks or system tools) set their own `TOPMOST` flag which can appear above the overlay. Calling `root.lift()` re-asserts z-order each time the overlay becomes visible. |
| Fixed height | Long sentences wrap within 2 lines. Text beyond that is cropped by `wraplength`. |
