from dataclasses import dataclass, field

import questionary
from questionary import Style as QStyle

TARGET_RATE: int = 16_000
CHUNK: int = 512

WIZARD_STYLE = QStyle([
    ("qmark",       "fg:#00bcd4 bold"),
    ("question",    "bold white"),
    ("answer",      "fg:#00bcd4 bold"),
    ("pointer",     "fg:#00bcd4 bold"),
    ("highlighted", "fg:#00bcd4 bold"),
    ("selected",    "fg:#00bcd4"),
    ("separator",   "fg:#555555"),
    ("instruction", "fg:#555555 italic"),
])

MODEL_CHOICES = [
    questionary.Choice("Fast      – tiny.en    (fastest, lower accuracy)",        value="tiny.en"),
    questionary.Choice("Balanced  – small.en   (recommended)  ★",                 value="small.en"),
    questionary.Choice("Accurate  – medium.en  (higher accuracy, more VRAM)",     value="medium.en"),
    questionary.Choice("Best      – large-v2   (most accurate, most resources)",  value="large-v2"),
]

REALTIME_MODEL_CHOICES = [
    questionary.Choice("Fastest   – tiny.en   (recommended)  ★",                 value="tiny.en"),
    questionary.Choice("Balanced  – base.en   (slightly better realtime accuracy)", value="base.en"),
    questionary.Choice("Accurate  – small.en  (best realtime accuracy)",          value="small.en"),
]


@dataclass
class Config:
    device_name: str     = ""
    model: str           = "tiny.en"
    realtime_model: str  = "tiny.en"
    compute: str         = "cuda"
    language: str        = "en"
    show_resources: bool = True
    max_history: int     = 100
    save_to_file: bool   = False
    output_file: str     = ""
    show_overlay: bool   = False
