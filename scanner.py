from pathlib import Path

SUPPORTED = (
    ".mp3",
    ".flac",
    ".m4a",
    ".ogg",
    ".opus",
    ".wav"
)

def scan_library(root):

    root = Path(root)

    files = [
        f for f in root.rglob("*")
        if f.is_file() and f.suffix.lower() in SUPPORTED
    ]

    return sorted(files)