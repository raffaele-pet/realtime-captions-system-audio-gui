"""Interactive two-page setup wizard (questionary-powered).

Collects all user preferences and returns a fully populated Config.
"""

import os
import sys
import time

import pyaudiowpatch as pyaudio
import pynvml
import questionary
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .config import (
    Config,
    MODEL_CHOICES,
    REALTIME_MODEL_CHOICES,
    WIZARD_STYLE,
)

console = Console()

TRANSCRIPTS_DIR = "transcripts"


def _detect_cuda() -> bool:
    try:
        pynvml.nvmlInit()
        ok = pynvml.nvmlDeviceGetCount() > 0
        pynvml.nvmlShutdown()
        return ok
    except pynvml.NVMLError:
        return False


def _wizard_header(title: str, subtitle: str = "", step: str = "") -> None:
    console.print()
    content = Text()
    if step:
        content.append(f"{step}\n", style="dim")
    content.append(title, style="bold cyan")
    if subtitle:
        content.append(f"\n{subtitle}", style="dim")
    console.print(Panel(content, border_style="cyan", padding=(0, 4)))
    console.print()


def run_wizard() -> Config:
    cfg          = Config()
    cuda_present = _detect_cuda()

    # ── Page 1 : Audio source ─────────────────────────────────────────────────
    console.clear()
    _wizard_header(
        "Realtime Speech Transcription",
        "System audio  →  Whisper speech-to-text",
        "Step 1 of 2  –  Select audio source",
    )

    p       = pyaudio.PyAudio()
    devices = list(p.get_loopback_device_info_generator())
    p.terminate()

    if not devices:
        console.print("[bold red]No WASAPI loopback devices found.[/bold red]")
        console.print("[dim]Ensure an output device is active and your drivers support WASAPI loopback.[/dim]")
        sys.exit(1)

    tbl = Table(box=box.ROUNDED, border_style="bright_black", padding=(0, 1))
    tbl.add_column("#",        style="dim",  width=3, justify="right")
    tbl.add_column("Device",   style="cyan")
    tbl.add_column("Rate",     style="dim",  justify="right")
    tbl.add_column("Channels", style="dim",  justify="right")
    for i, d in enumerate(devices, 1):
        tbl.add_row(
            str(i),
            d["name"].replace(" [Loopback]", ""),
            f"{int(d['defaultSampleRate'])} Hz",
            str(d["maxInputChannels"]),
        )
    console.print(tbl)
    console.print()

    cfg.device_name = questionary.select(
        "Select audio source to transcribe:",
        choices=[
            questionary.Choice(
                f"{d['name'].replace(' [Loopback]', '')}  "
                f"[{int(d['defaultSampleRate'])} Hz  ·  {d['maxInputChannels']}ch]",
                value=d["name"],
            )
            for d in devices
        ],
        style=WIZARD_STYLE,
    ).ask() or sys.exit(0)  # type: ignore[func-returns-value]

    # ── Page 2 : Options ──────────────────────────────────────────────────────
    console.print()
    _wizard_header(
        "Configuration",
        "Tune accuracy, speed and display preferences",
        "Step 2 of 2  –  Options",
    )

    cfg.model = questionary.select(
        "Transcription model  (final accuracy):",
        choices=MODEL_CHOICES,
        default=MODEL_CHOICES[0],
        style=WIZARD_STYLE,
    ).ask() or sys.exit(0)  # type: ignore[func-returns-value]

    cfg.realtime_model = questionary.select(
        "Real-time preview model  (live display):",
        choices=REALTIME_MODEL_CHOICES,
        default=REALTIME_MODEL_CHOICES[0],
        style=WIZARD_STYLE,
    ).ask() or sys.exit(0)  # type: ignore[func-returns-value]

    compute_choices = []
    if cuda_present:
        compute_choices.append(questionary.Choice("CUDA  – GPU accelerated  (recommended)  ★", value="cuda"))
    compute_choices.append(questionary.Choice("CPU   – No GPU required", value="cpu"))
    cfg.compute = questionary.select(
        "Compute device:",
        choices=compute_choices,
        style=WIZARD_STYLE,
    ).ask() or sys.exit(0)  # type: ignore[func-returns-value]

    cfg.language = questionary.select(
        "Transcription language:",
        choices=[
            questionary.Choice("English        (en)  ★", value="en"),
            questionary.Choice("Auto-detect    (slower first transcription)", value=""),
        ],
        style=WIZARD_STYLE,
    ).ask() or sys.exit(0)  # type: ignore[func-returns-value]

    cfg.show_resources = questionary.confirm(
        "Show CPU / RAM / GPU resource monitor?",
        default=True,
        style=WIZARD_STYLE,
    ).ask()
    if cfg.show_resources is None:
        sys.exit(0)

    cfg.save_to_file = questionary.confirm(
        "Save transcription to a .txt file?",
        default=False,
        style=WIZARD_STYLE,
    ).ask()
    if cfg.save_to_file is None:
        sys.exit(0)

    if cfg.save_to_file:
        default_name = f"transcript_{time.strftime('%Y%m%d_%H%M%S')}"
        raw = questionary.text(
            "Output filename:",
            default=default_name,
            instruction="(press Enter to use the default · .txt added automatically)",
            validate=lambda v: "Filename cannot be empty." if not v.strip() else True,
            style=WIZARD_STYLE,
        ).ask()
        if raw is None:
            sys.exit(0)
        name = os.path.basename(raw.strip())
        if not name.endswith(".txt"):
            name = f"{name}.txt"
        os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
        cfg.output_file = os.path.join(TRANSCRIPTS_DIR, name)

    cfg.show_overlay = questionary.confirm(
        "Show floating caption overlay? (visible over all apps, click-through)",
        default=False,
        style=WIZARD_STYLE,
    ).ask()
    if cfg.show_overlay is None:
        sys.exit(0)

    # ── Summary + confirm ─────────────────────────────────────────────────────
    console.print()
    summary = Table.grid(padding=(0, 2))
    summary.add_column(style="dim",      min_width=20)
    summary.add_column(style="bold cyan")
    summary.add_row("Audio source",    cfg.device_name.replace(" [Loopback]", ""))
    summary.add_row("Model",           cfg.model)
    summary.add_row("Realtime model",  cfg.realtime_model)
    summary.add_row("Compute",         cfg.compute.upper())
    summary.add_row("Language",        cfg.language or "auto-detect")
    summary.add_row("Resources panel", "Enabled" if cfg.show_resources else "Disabled")
    summary.add_row(
        "Save to file",
        cfg.output_file if cfg.save_to_file else "[dim]No[/dim]",
    )
    summary.add_row("Caption overlay", "Enabled" if cfg.show_overlay else "[dim]No[/dim]")
    console.print(Panel(summary, title="[bold] Summary [/bold]", border_style="bright_black", padding=(0, 2)))
    console.print()

    if not questionary.confirm("Start transcription?", default=True, style=WIZARD_STYLE).ask():
        sys.exit(0)

    return cfg
