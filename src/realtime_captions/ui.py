"""Rich terminal UI: panels, resource bars, and the refresh loop."""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING

from rich import box
from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .config import Config
from .state import Resources, get_snapshot

if TYPE_CHECKING:
    from .overlay import CaptionOverlay


# ── resource bar helpers ──────────────────────────────────────────────────────
def _pct_bar(pct: float, width: int = 12) -> Text:
    color  = "green" if pct < 50 else ("yellow" if pct < 80 else "red")
    filled = round(width * pct / 100)
    bar    = Text(no_wrap=True, overflow="crop")
    bar.append("█" * filled,          style=f"bold {color}")
    bar.append("░" * (width - filled), style="dim")
    return bar


def _temp_style(temp: float) -> str:
    return "green" if temp < 65 else ("yellow" if temp < 80 else "bold red")


def _make_resources_panel(r: Resources) -> Panel:
    grid = Table.grid(padding=(0, 3))
    grid.add_column(min_width=34)
    grid.add_column(min_width=34)

    grid.add_row(
        Text.assemble(("CPU  ", "dim"), _pct_bar(r.cpu_pct),  (f"  {r.cpu_pct:5.1f}%", "")),
        Text.assemble(("RAM  ", "dim"), _pct_bar(r.ram_pct),  (f"  {r.ram_used_gb:5.1f} / {r.ram_total_gb:.1f} GB", "")),
    )

    if r.gpu_pct is not None:
        grid.add_row(
            Text.assemble(
                ("GPU  ", "dim"), _pct_bar(r.gpu_pct),
                (f"  {r.gpu_pct:5.1f}%  ", ""),
                (f"{r.gpu_temp:.0f}°C", _temp_style(r.gpu_temp)),  # type: ignore[arg-type]
            ),
            Text.assemble(
                ("VRAM ", "dim"), _pct_bar(r.gpu_mem_pct),  # type: ignore[arg-type]
                (f"  {r.gpu_mem_used_gb:5.1f} / {r.gpu_mem_total_gb:.1f} GB", ""),
            ),
        )
        title = f"[bold] System  [dim]{r.gpu_name}[/dim] [/bold]"
    else:
        title = "[bold] System [/bold]"

    return Panel(grid, title=title, border_style="bright_black", padding=(0, 2))


# ── main UI builder ───────────────────────────────────────────────────────────
def make_ui(cfg: Config) -> Group:
    live, stable, status, history, res = get_snapshot()

    device_short = cfg.device_name.replace(" [Loopback]", "")

    if status == "Recording":
        dot_sym, dot_style    = "●", "bold red"
        status_label, status_style = "Recording", "bold red"
    elif status == "Listening":
        dot_sym, dot_style    = "●", "bold green"
        status_label, status_style = "Listening", "bold green"
    else:
        dot_sym, dot_style    = "○", "dim"
        status_label, status_style = status, "dim"

    header_parts: list[tuple[str, str]] = [
        (" ", ""), (dot_sym, dot_style), (" ", ""),
        (status_label, status_style),
        ("   │   ", "dim"), (device_short, "bold cyan"),
        ("   │   ", "dim"), (f"model: {cfg.model}", "dim"),
    ]
    if cfg.save_to_file:
        header_parts += [("   │   ", "dim"), (f"saving → {cfg.output_file}", "bold green")]
    header_parts += [("   │   ", "dim"), ("Ctrl+C to stop", "dim")]

    header = Panel(
        Text.assemble(*header_parts),
        box=box.HORIZONTALS,
        border_style="bright_black",
        padding=(0, 1),
    )

    current = stable or live
    current_panel = Panel(
        Text(current, style="bold white", overflow="fold")
        if current else
        Text("Waiting for speech…", style="dim italic", justify="center"),
        title="[bold cyan] ◉  Live [/bold cyan]",
        border_style="cyan",
        padding=(1, 3),
        height=9,
    )

    history_panel = Panel(
        Group(*[
            Text.assemble((f" {ts} ", "dim green"), ("│ ", "dim"), (text, "white"))
            for ts, text in reversed(history)
        ]) if history else Text("Completed sentences will appear here.", style="dim italic", justify="center"),
        title="[bold] ≡  History [/bold]",
        border_style="bright_black",
        padding=(0, 2),
    )

    parts: list = [header]
    if cfg.show_resources:
        parts.append(_make_resources_panel(res))
    parts += [current_panel, history_panel]
    return Group(*parts)


# ── refresh loop ──────────────────────────────────────────────────────────────
def refresh_loop(
    live_display: Live,
    cfg: Config,
    overlay: CaptionOverlay | None,
    stop_event: threading.Event,
) -> None:
    while not stop_event.is_set():
        live_display.update(make_ui(cfg))
        if overlay is not None:
            live_text, stable, *_ = get_snapshot()
            overlay.set_text(stable or live_text)
        time.sleep(0.1)
