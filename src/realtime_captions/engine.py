"""Reusable transcription engine for the graphical interface."""

from __future__ import annotations

import logging
import os
import threading
import time
from collections.abc import Callable

from RealtimeSTT import AudioToTextRecorder

from .audio import on_live, on_recording_start, on_recording_stop, on_stable, stream_loopback
from .config import Config
from .overlay import CaptionOverlay
from .resources import resource_monitor
from .state import append_history, clear_live, get_snapshot, reset_history, set_status


class TranscriptionSession:
    """Own one recorder instance and expose a thread-safe stop operation."""

    def __init__(self, on_final: Callable[[str, str], None] | None = None) -> None:
        self.stop_event = threading.Event()
        self.recorder: AudioToTextRecorder | None = None
        self.on_final = on_final

    def stop(self) -> None:
        self.stop_event.set()
        recorder = self.recorder
        if recorder is not None:
            try:
                recorder.abort()
            except Exception:
                pass

    def run(self, cfg: Config) -> None:
        reset_history(cfg.max_history)
        os.makedirs("transcripts", exist_ok=True)
        output_file = open(cfg.output_file, "a", encoding="utf-8") if cfg.save_to_file else None
        overlay: CaptionOverlay | None = None

        try:
            if cfg.show_overlay:
                overlay = CaptionOverlay()
                overlay.start()
                threading.Thread(
                    target=self._sync_overlay,
                    args=(overlay,),
                    daemon=True,
                ).start()

            if output_file:
                output_file.write(f"# Transcription started {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                output_file.write(f"# Source : {cfg.device_name}\n# Model  : {cfg.model}\n\n")
                output_file.flush()

            set_status("Caricamento modello…")
            with AudioToTextRecorder(
                model=cfg.model,
                language=cfg.language,
                device=cfg.compute,
                use_microphone=False,
                spinner=False,
                level=logging.CRITICAL,
                no_log_file=True,
                enable_realtime_transcription=True,
                use_main_model_for_realtime=True,
                realtime_model_type=cfg.realtime_model,
                realtime_processing_pause=0.15,
                on_realtime_transcription_update=on_live,
                on_realtime_transcription_stabilized=on_stable,
                on_recording_start=on_recording_start,
                on_recording_stop=on_recording_stop,
            ) as recorder:
                self.recorder = recorder
                set_status("In ascolto")
                threading.Thread(target=resource_monitor, args=(self.stop_event,), daemon=True).start()
                threading.Thread(
                    target=stream_loopback,
                    args=(recorder, cfg.device_name, self.stop_event),
                    daemon=True,
                ).start()

                while not self.stop_event.is_set():
                    final_text = recorder.text().strip()
                    if not final_text:
                        continue
                    timestamp = time.strftime("%H:%M:%S")
                    append_history(timestamp, final_text)
                    clear_live()
                    if overlay is not None:
                        overlay.set_text("")
                    if output_file:
                        output_file.write(f"[{timestamp}] {final_text}\n")
                        output_file.flush()
                    if self.on_final:
                        self.on_final(timestamp, final_text)
        finally:
            self.recorder = None
            self.stop_event.set()
            set_status("Fermato")
            if overlay is not None:
                overlay.set_text("")
                overlay.stop()
            if output_file:
                output_file.write(f"\n# Transcription ended {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                output_file.close()

    def _sync_overlay(self, overlay: CaptionOverlay) -> None:
        """Mirror live transcription state into the floating caption window."""
        while not self.stop_event.wait(0.08):
            live, stable, _status, _history, _resources = get_snapshot()
            overlay.set_text(live or stable)
