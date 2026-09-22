"""Modern, dependency-free Tkinter interface for Realtime Captions."""

from __future__ import annotations

import os
import logging
import ctypes
import queue
import subprocess
import threading
import time
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter import font as tkfont

import pyaudiowpatch as pyaudio

from .config import Config
from .engine import TranscriptionSession
from .state import get_snapshot

APP_DIR = Path(__file__).resolve().parents[2]
LOG_FILE = APP_DIR / "logs" / "realtime-captions.log"
LOG_FILE.parent.mkdir(exist_ok=True)
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8",
)
MODELS = {
    "tiny.en": ("Veloce", "~75 MB · ideale per CPU"),
    "small.en": ("Bilanciato", "~460 MB · consigliato"),
    "medium.en": ("Accurato", "~1,5 GB · qualità superiore"),
}
MODEL_REPOS = {name: f"Systran/faster-whisper-{name}" for name in MODELS}

BG = "#0b1020"
SURFACE = "#141b2d"
SURFACE_2 = "#1b253b"
TEXT = "#f5f7fb"
MUTED = "#9aa8c2"
ACCENT = "#5eead4"
ACCENT_DARK = "#0f766e"
DANGER = "#fb7185"


def _latest_wrapped_lines(text: str, font: tkfont.Font, width: int, max_lines: int) -> str:
    """Wrap using real font metrics and return only the newest visible lines."""
    if not text:
        return ""
    lines: list[str] = []
    current = ""
    for word in text.replace("\n", " \n ").split():
        if word == "\n":
            if current:
                lines.append(current)
                current = ""
            continue
        candidate = f"{current} {word}".strip()
        if current and font.measure(candidate) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return "\n".join(lines[-max_lines:])


def _installed_models() -> set[str]:
    try:
        from huggingface_hub import scan_cache_dir

        cached = {repo.repo_id for repo in scan_cache_dir().repos}
        return {name for name, repo_id in MODEL_REPOS.items() if repo_id in cached}
    except Exception:
        return set()


class FloatingCaptionOverlay:
    """Caption overlay sharing the GUI's Tcl event loop (no second Tk thread)."""

    def __init__(self, root: tk.Tk) -> None:
        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.attributes("-alpha", 0.0)
        self.window.configure(bg="#0e0e0e")
        width = min(int(root.winfo_screenwidth() * 0.72), 1280)
        self.screen_height = root.winfo_screenheight()
        self.width = width
        self.caption_font = tkfont.Font(self.window, family="Segoe UI", size=18, weight="bold")
        self.label = tk.Label(
            self.window, text="", bg="#0e0e0e", fg="#ffff00",
            font=self.caption_font, wraplength=width - 56,
            justify="left", anchor="w", padx=28, pady=12,
        )
        self.label.pack(fill="both", expand=True)
        self._place(72)
        self.window.after(200, self._make_click_through)

    def _place(self, height: int) -> None:
        x = (self.window.winfo_screenwidth() - self.width) // 2
        y = self.screen_height - height - 72
        self.window.geometry(f"{self.width}x{height}+{x}+{y}")

    def _make_click_through(self) -> None:
        try:
            hwnd = ctypes.windll.user32.GetAncestor(self.window.winfo_id(), 2)
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x20 | 0x80)
        except Exception:
            pass

    def set_text(self, text: str) -> None:
        if not self.window.winfo_exists():
            return
        if not text:
            self.window.attributes("-alpha", 0.0)
            return
        latest = _latest_wrapped_lines(text, self.caption_font, self.width - 56, 5)
        self.label.configure(text=latest)
        self.window.update_idletasks()
        height = max(72, min(self.label.winfo_reqheight(), 210))
        self._place(height)
        self.window.attributes("-alpha", 0.88)
        self.window.lift()

    def close(self) -> None:
        try:
            self.window.destroy()
        except tk.TclError:
            pass


class CaptionsGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.session: TranscriptionSession | None = None
        self.worker: threading.Thread | None = None
        self.downloading = False
        self.ui_events: queue.Queue = queue.Queue()
        self.overlay: FloatingCaptionOverlay | None = None
        self.devices: dict[str, str] = {}
        self.installed = _installed_models()

        root.title("Realtime Captions")
        root.geometry("1080x720")
        root.minsize(900, 620)
        root.configure(bg=BG)
        root.protocol("WM_DELETE_WINDOW", self._close)
        icon = APP_DIR / "assets" / "chat-room.ico"
        if icon.exists():
            try:
                root.iconbitmap(str(icon))
            except tk.TclError:
                pass

        self._make_style()
        self._build()
        self._refresh_devices()
        self._refresh_model_status()
        self._poll_state()

    def _make_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=SURFACE_2, background=SURFACE_2,
                        foreground=TEXT, arrowcolor=ACCENT, padding=9)
        style.map("TCombobox", fieldbackground=[("readonly", SURFACE_2)],
                  foreground=[("readonly", TEXT)])
        style.configure("TCheckbutton", background=SURFACE, foreground=TEXT,
                        focuscolor=SURFACE, font=("Segoe UI", 10))
        style.map("TCheckbutton", background=[("active", SURFACE)])
        style.configure("Accent.Horizontal.TProgressbar", troughcolor=SURFACE_2,
                        background=ACCENT, bordercolor=SURFACE_2, lightcolor=ACCENT,
                        darkcolor=ACCENT)

    def _build(self) -> None:
        top = tk.Frame(self.root, bg=BG, padx=34, pady=24)
        top.pack(fill="x")
        tk.Label(top, text="Realtime Captions", bg=BG, fg=TEXT,
                 font=("Segoe UI Semibold", 24)).pack(side="left")
        tk.Label(top, text="Trascrizione privata, locale e in tempo reale", bg=BG,
                 fg=MUTED, font=("Segoe UI", 10)).pack(side="left", padx=18, pady=(10, 0))
        self.status_pill = tk.Label(top, text="● Pronto", bg="#132f36", fg=ACCENT,
                                    font=("Segoe UI Semibold", 10), padx=14, pady=7)
        self.status_pill.pack(side="right")

        body = tk.Frame(self.root, bg=BG, padx=34)
        body.pack(fill="both", expand=True, pady=(0, 30))
        body.grid_columnconfigure(0, weight=0, minsize=360)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        settings = tk.Frame(body, bg=SURFACE, padx=24, pady=22)
        settings.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        tk.Label(settings, text="Configurazione", bg=SURFACE, fg=TEXT,
                 font=("Segoe UI Semibold", 15)).pack(anchor="w")
        tk.Label(settings, text="Sorgente audio", bg=SURFACE, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(22, 7))
        device_row = tk.Frame(settings, bg=SURFACE)
        device_row.pack(fill="x")
        self.device_box = ttk.Combobox(device_row, state="readonly", font=("Segoe UI", 10))
        self.device_box.pack(side="left", fill="x", expand=True)
        self._button(device_row, "↻", self._refresh_devices, compact=True).pack(side="left", padx=(8, 0))

        tk.Label(settings, text="Modello Whisper attivo", bg=SURFACE, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(20, 7))
        self.model_var = tk.StringVar(value="tiny.en")
        self.model_box = ttk.Combobox(settings, state="readonly", textvariable=self.model_var,
                                      values=list(MODELS), font=("Segoe UI", 10))
        self.model_box.pack(fill="x")
        self.model_box.bind("<<ComboboxSelected>>", lambda _e: self._refresh_model_status())
        self.model_hint = tk.Label(settings, bg=SURFACE, fg=MUTED, font=("Segoe UI", 9), anchor="w")
        self.model_hint.pack(fill="x", pady=(7, 0))

        model_actions = tk.Frame(settings, bg=SURFACE)
        model_actions.pack(fill="x", pady=(12, 0))
        self.download_one = self._button(model_actions, "Scarica selezionato", self._download_selected)
        self.download_one.pack(side="left", fill="x", expand=True)
        self.download_all = self._button(model_actions, "Scarica tutti e 3", self._download_all)
        self.download_all.pack(side="left", fill="x", expand=True, padx=(8, 0))

        self.progress = ttk.Progressbar(settings, mode="indeterminate", style="Accent.Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(12, 0))
        self.download_label = tk.Label(settings, text="", bg=SURFACE, fg=MUTED,
                                       font=("Segoe UI", 8), anchor="w", wraplength=305)
        self.download_label.pack(fill="x", pady=(5, 0))

        options = tk.Frame(settings, bg=SURFACE)
        options.pack(fill="x", pady=(18, 0))
        self.overlay_var = tk.BooleanVar(value=True)
        self.save_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options, text="Sottotitoli sovrapposti", variable=self.overlay_var).pack(anchor="w")
        ttk.Checkbutton(options, text="Salva trascrizione in .txt", variable=self.save_var).pack(anchor="w", pady=(6, 0))

        compute_row = tk.Frame(settings, bg=SURFACE)
        compute_row.pack(fill="x", pady=(18, 0))
        tk.Label(compute_row, text="Elaborazione", bg=SURFACE, fg=MUTED,
                 font=("Segoe UI", 9)).pack(side="left")
        self.compute_var = tk.StringVar(value="cuda")
        self.compute_box = ttk.Combobox(compute_row, state="readonly", width=9,
                                        textvariable=self.compute_var, values=("cpu", "cuda"))
        self.compute_box.pack(side="right")

        controls = tk.Frame(settings, bg=SURFACE)
        controls.pack(side="bottom", fill="x", pady=(24, 0))
        self.start_btn = self._button(controls, "Avvia trascrizione", self._start, accent=True)
        self.start_btn.pack(side="left", fill="x", expand=True)
        self.stop_btn = self._button(controls, "Stop ascolto", self._stop, danger=True)
        self.stop_btn.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self.stop_btn.configure(state="disabled")

        content = tk.Frame(body, bg=BG)
        content.grid(row=0, column=1, sticky="nsew")
        content.grid_rowconfigure(1, weight=1)
        content.grid_columnconfigure(0, weight=1)

        live_card = tk.Frame(content, bg=SURFACE, padx=24, pady=19)
        live_card.grid(row=0, column=0, sticky="ew")
        tk.Label(live_card, text="IN TEMPO REALE", bg=SURFACE, fg=ACCENT,
                 font=("Segoe UI Semibold", 9)).pack(anchor="w")
        self.live_font = tkfont.Font(self.root, family="Segoe UI", size=16)
        self.live_label = tk.Label(live_card, text="In attesa dell’audio…", bg=SURFACE, fg=TEXT,
                                   font=self.live_font, justify="left", anchor="nw",
                                   wraplength=570, height=3)
        self.live_label.pack(fill="x", pady=(12, 0))

        history_card = tk.Frame(content, bg=SURFACE, padx=24, pady=18)
        history_card.grid(row=1, column=0, sticky="nsew", pady=(14, 0))
        history_head = tk.Frame(history_card, bg=SURFACE)
        history_head.pack(fill="x")
        tk.Label(history_head, text="Trascrizione", bg=SURFACE, fg=TEXT,
                 font=("Segoe UI Semibold", 14)).pack(side="left")
        self._button(history_head, "Apri cartella", self._open_transcripts, compact=True).pack(side="right")
        self.history = tk.Text(history_card, bg=SURFACE, fg="#dbe5f5", insertbackground=TEXT,
                               relief="flat", borderwidth=0, font=("Segoe UI", 11),
                               wrap="word", padx=0, pady=14, state="disabled")
        self.history.pack(fill="both", expand=True)
        self.history.tag_configure("time", foreground=ACCENT, font=("Segoe UI Semibold", 9))
        self.history.tag_configure("text", foreground="#dbe5f5", spacing3=10)

        footer = tk.Frame(history_card, bg=SURFACE)
        footer.pack(fill="x")
        self.resources_label = tk.Label(footer, text="CPU —  •  RAM —", bg=SURFACE, fg=MUTED,
                                        font=("Segoe UI", 9))
        self.resources_label.pack(side="left")
        tk.Label(footer, text="L’audio non lascia mai il computer", bg=SURFACE, fg=MUTED,
                 font=("Segoe UI", 9)).pack(side="right")

    def _button(self, parent: tk.Widget, text: str, command, *, accent=False, danger=False, compact=False) -> tk.Button:
        bg = ACCENT_DARK if accent else ("#7f1d3a" if danger else SURFACE_2)
        active = "#115e59" if accent else ("#9f1239" if danger else "#263550")
        return tk.Button(parent, text=text, command=command, bg=bg, fg=TEXT,
                         activebackground=active, activeforeground=TEXT, relief="flat",
                         borderwidth=0, cursor="hand2", font=("Segoe UI Semibold", 9 if compact else 10),
                         padx=10 if compact else 14, pady=7 if compact else 10)

    def _refresh_devices(self) -> None:
        try:
            pa = pyaudio.PyAudio()
            try:
                devices = list(pa.get_loopback_device_info_generator())
            finally:
                pa.terminate()
            self.devices = {
                f"{d['name'].replace(' [Loopback]', '')}  ·  {int(d['defaultSampleRate'])} Hz": d["name"]
                for d in devices
            }
            self.device_box["values"] = list(self.devices)
            if self.devices:
                self.device_box.current(0)
            else:
                self.device_box.set("Nessun dispositivo loopback trovato")
        except Exception as exc:
            self.device_box.set("Errore audio")
            messagebox.showerror("Dispositivi audio", str(exc))

    def _refresh_model_status(self) -> None:
        selected = self.model_var.get()
        title, detail = MODELS[selected]
        status = "installato ✓" if selected in self.installed else "da scaricare"
        self.model_hint.configure(text=f"{title} · {detail} · {status}", fg=ACCENT if selected in self.installed else MUTED)
        self.download_one.configure(text="Già installato" if selected in self.installed else "Scarica selezionato")

    def _download_selected(self) -> None:
        self._download_models([self.model_var.get()])

    def _download_all(self) -> None:
        self._download_models(list(MODELS))

    def _download_models(self, models: list[str], start_after: bool = False) -> None:
        if self.downloading:
            return
        pending = [m for m in models if m not in self.installed]
        if not pending:
            if start_after:
                self._start_engine()
            else:
                self.download_label.configure(text="I modelli scelti sono già disponibili.")
            return
        self.downloading = True
        self.progress.start(12)
        self.download_one.configure(state="disabled")
        self.download_all.configure(state="disabled")

        def job() -> None:
            error = None
            try:
                from huggingface_hub import snapshot_download
                for index, model in enumerate(pending, 1):
                    self.ui_events.put(lambda m=model, i=index: self.download_label.configure(
                        text=f"Download {m} ({i}/{len(pending)})… il primo avvio può richiedere qualche minuto."))
                    snapshot_download(repo_id=MODEL_REPOS[model])
                    self.installed.add(model)
            except Exception as exc:
                logging.error("Download modello non riuscito:\n%s", traceback.format_exc())
                error = f"{exc}\n\nDettagli salvati in:\n{LOG_FILE}"
            self.ui_events.put(lambda e=error, s=start_after: self._download_finished(e, s))

        threading.Thread(target=job, daemon=True).start()

    def _download_finished(self, error: str | None, start_after: bool) -> None:
        self.downloading = False
        self.progress.stop()
        self.download_one.configure(state="normal")
        self.download_all.configure(state="normal")
        self._refresh_model_status()
        if error:
            self.download_label.configure(text="Download non riuscito.")
            messagebox.showerror("Download modello", error)
        else:
            self.download_label.configure(text="Download completato. I modelli restano disponibili offline.")
            if start_after:
                self._start_engine()

    def _start(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        if not self.devices or self.device_box.get() not in self.devices:
            messagebox.showwarning("Sorgente audio", "Seleziona un dispositivo audio valido.")
            return
        selected = self.model_var.get()
        if selected not in self.installed:
            self.download_label.configure(text=f"Scarico automaticamente {selected} prima dell’avvio…")
            self._download_models([selected], start_after=True)
            return
        self._start_engine()

    def _start_engine(self) -> None:
        stamp = time.strftime("%Y%m%d_%H%M%S")
        cfg = Config(
            device_name=self.devices[self.device_box.get()],
            model=self.model_var.get(),
            realtime_model=self.model_var.get(),
            compute=self.compute_var.get(),
            language="en",
            show_resources=True,
            save_to_file=self.save_var.get(),
            output_file=str(APP_DIR / "transcripts" / f"transcript_{stamp}.txt"),
            # The GUI owns the overlay so every Tk operation stays on the main thread.
            show_overlay=False,
        )
        if self.overlay_var.get():
            self.overlay = FloatingCaptionOverlay(self.root)
        self.session = TranscriptionSession()
        self.worker = threading.Thread(target=self._engine_job, args=(cfg,), daemon=True)
        self.worker.start()
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.device_box.configure(state="disabled")
        self.model_box.configure(state="disabled")

    def _engine_job(self, cfg: Config) -> None:
        error = None
        try:
            os.chdir(APP_DIR)
            assert self.session is not None
            self.session.run(cfg)
        except Exception as exc:
            error = str(exc)
        self.ui_events.put(lambda e=error: self._engine_finished(e))

    def _engine_finished(self, error: str | None) -> None:
        if self.overlay:
            self.overlay.close()
            self.overlay = None
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.device_box.configure(state="readonly")
        self.model_box.configure(state="readonly")
        if error:
            messagebox.showerror("Realtime Captions", error)

    def _stop(self) -> None:
        if self.session:
            self.session.stop()
        self.status_pill.configure(text="● Arresto…", bg="#342432", fg=DANGER)

    def _poll_state(self) -> None:
        try:
            while True:
                self.ui_events.get_nowait()()
        except queue.Empty:
            pass
        live, stable, status, history, resources = get_snapshot()
        shown = live or stable or "In attesa dell’audio…"
        live_width = max(240, self.live_label.winfo_width() - 8)
        latest = _latest_wrapped_lines(shown, self.live_font, live_width, 3)
        self.live_label.configure(text=latest, fg=TEXT if live or stable else MUTED)
        if self.overlay:
            self.overlay.set_text(live or stable)
        color = ACCENT if status in ("In ascolto", "Listening", "Recording") else MUTED
        self.status_pill.configure(text=f"● {status}", fg=color)
        current_count = int(self.history.index("end-1c").split(".")[0]) - 1
        if len(history) != current_count:
            self.history.configure(state="normal")
            self.history.delete("1.0", "end")
            for timestamp, text in history:
                self.history.insert("end", f"{timestamp}  ", "time")
                self.history.insert("end", f"{text}\n", "text")
            self.history.see("end")
            self.history.configure(state="disabled")
        gpu = f"  •  GPU {resources.gpu_pct:.0f}%" if resources.gpu_pct is not None else ""
        self.resources_label.configure(
            text=f"CPU {resources.cpu_pct:.0f}%  •  RAM {resources.ram_pct:.0f}%{gpu}")
        self.root.after(220, self._poll_state)

    def _open_transcripts(self) -> None:
        folder = APP_DIR / "transcripts"
        folder.mkdir(exist_ok=True)
        subprocess.Popen(["explorer", str(folder)])

    def _close(self) -> None:
        if self.session:
            self.session.stop()
        if self.overlay:
            self.overlay.close()
        self.root.destroy()


def run_gui() -> None:
    root = tk.Tk()
    CaptionsGUI(root)
    root.mainloop()
