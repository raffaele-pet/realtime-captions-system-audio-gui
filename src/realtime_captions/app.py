"""Application orchestrator.

Wires all subsystems together, starts background threads, and runs
the main recorder loop. Entry point for `main.py`.
"""

import logging
import sys
import threading
import time

from rich.console import Console
from rich.live import Live
from RealtimeSTT import AudioToTextRecorder

from .audio import on_live, on_stable, on_recording_start, on_recording_stop, stream_loopback
from .config import Config
from .overlay import CaptionOverlay
from .resources import resource_monitor
from .state import reset_history, set_status, append_history, clear_live
from .ui import make_ui, refresh_loop
from .wizard import run_wizard

console = Console()


def run() -> None:
    try:
        cfg = run_wizard()
    except KeyboardInterrupt:
        console.print("\n[dim]Cancelled.[/dim]")
        sys.exit(0)

    reset_history(cfg.max_history)
    stop_event = threading.Event()

    output_file = open(cfg.output_file, "a", encoding="utf-8") if cfg.save_to_file else None  # noqa: SIM115

    overlay: CaptionOverlay | None = None
    if cfg.show_overlay:
        overlay = CaptionOverlay()
        overlay.start()

    if output_file:
        output_file.write(f"# Transcription started {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        output_file.write(f"# Source : {cfg.device_name}\n")
        output_file.write(f"# Model  : {cfg.model}\n\n")
        output_file.flush()

    with AudioToTextRecorder(
        model=cfg.model,
        language=cfg.language,
        device=cfg.compute,
        use_microphone=False,
        spinner=False,
        level=logging.CRITICAL,
        no_log_file=True,
        enable_realtime_transcription=True,
        realtime_model_type=cfg.realtime_model,
        realtime_processing_pause=0.15,
        on_realtime_transcription_update=on_live,
        on_realtime_transcription_stabilized=on_stable,
        on_recording_start=on_recording_start,
        on_recording_stop=on_recording_stop,
    ) as recorder:
        set_status("Listening")

        for target, args in [
            (resource_monitor,  (stop_event,)),
            (stream_loopback,   (recorder, cfg.device_name, stop_event)),
        ]:
            threading.Thread(target=target, args=args, daemon=True).start()

        with Live(make_ui(cfg), screen=True, refresh_per_second=10) as live_display:
            threading.Thread(
                target=refresh_loop,
                args=(live_display, cfg, overlay, stop_event),
                daemon=True,
            ).start()

            try:
                while True:
                    final_text = recorder.text().strip()
                    if final_text:
                        ts = time.strftime("%H:%M:%S")
                        append_history(ts, final_text)
                        clear_live()
                        if output_file:
                            output_file.write(f"[{ts}] {final_text}\n")
                            output_file.flush()
            except KeyboardInterrupt:
                stop_event.set()
                set_status("Stopped")
                live_display.update(make_ui(cfg))
            finally:
                if overlay is not None:
                    overlay.set_text("")
                    overlay.stop()
                if output_file:
                    output_file.write(f"\n# Transcription ended {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    output_file.close()
