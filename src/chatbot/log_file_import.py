"""Safe, bounded reading of local NgSpice text logs for offline analysis."""
from pathlib import Path

MAX_LOG_BYTES = 128 * 1024  # Keep large logs out of the GUI and chat history.
MAX_LOG_LINES = 4000
ALLOWED_SUFFIXES = frozenset({".log", ".txt", ".out"})


def read_ngspice_log_file(filename: str | Path) -> str:
    """Read a small text log, preserving line numbers for diagnostics.

    The caller chooses the file explicitly through a file picker.  This
    function does not execute commands, inspect arbitrary directories, or
    transmit the data anywhere.
    """
    path = Path(filename)
    if path.suffix.lower() not in ALLOWED_SUFFIXES:
        raise ValueError("Choose a .log, .txt, or .out file.")
    if not path.is_file():
        raise ValueError("The selected log file was not found.")
    if path.stat().st_size > MAX_LOG_BYTES:
        raise ValueError("Log is too large (maximum 128 KiB).")

    # A second size check also catches files that grow after stat().
    with path.open("rb") as stream:
        data = stream.read(MAX_LOG_BYTES + 1)
    if len(data) > MAX_LOG_BYTES:
        raise ValueError("Log is too large (maximum 128 KiB).")
    if not data or b"\x00" in data:
        raise ValueError("The selected file is empty or not a text log.")

    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Older Windows NgSpice logs may use the Windows-1252 code page.
        text = data.decode("cp1252")

    if any(ord(ch) < 32 and ch not in "\r\n\t" for ch in text):
        raise ValueError("The selected file contains non-text control bytes.")
    if not text.strip():
        raise ValueError("The selected log file contains no messages.")
    if len(text.splitlines()) > MAX_LOG_LINES:
        raise ValueError("Log has too many lines (maximum 4000).")
    # Normalize Windows CRLF and legacy CR while keeping log line numbers.
    return text.replace("\r\n", "\n").replace("\r", "\n")
