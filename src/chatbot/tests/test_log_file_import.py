"""Regression tests for the bounded NgSpice log-import UI."""
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

SRC = Path(__file__).resolve().parents[2]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from chatbot.log_file_import import MAX_LOG_BYTES, read_ngspice_log_file


def test_valid_multiline_log_preserves_line_numbers(tmp_path):
    file = tmp_path / "simulation.log"
    file.write_text("Warning: singular matrix\nWarning: floating pins\n", encoding="utf-8")
    assert read_ngspice_log_file(file).splitlines() == [
        "Warning: singular matrix", "Warning: floating pins"
    ]


def test_utf8_bom(tmp_path):
    file = tmp_path / "simulation.TXT"
    file.write_bytes(b"\xef\xbb\xbfWarning: singular matrix\n")
    assert read_ngspice_log_file(file).startswith("Warning:")


def test_windows_encoding(tmp_path):
    file = tmp_path / "simulation.out"
    file.write_bytes("Error: node 1 \u2013 floating".encode("cp1252"))
    assert "floating" in read_ngspice_log_file(file)


def test_empty_log_is_rejected(tmp_path):
    file = tmp_path / "empty.log"
    file.write_text(" \n  \n")
    with pytest.raises(ValueError, match="no messages"):
        read_ngspice_log_file(file)


def test_large_log_is_rejected(tmp_path):
    file = tmp_path / "huge.log"
    file.write_bytes(b"X" * (MAX_LOG_BYTES + 1))
    with pytest.raises(ValueError, match="too large"):
        read_ngspice_log_file(file)


def test_binary_log_is_rejected(tmp_path):
    file = tmp_path / "binary.log"
    file.write_bytes(b"Warning:\x00\xff")
    with pytest.raises(ValueError, match="not a text"):
        read_ngspice_log_file(file)


def test_unknown_extension_is_rejected(tmp_path):
    file = tmp_path / "log.py"
    file.write_text("Warning: singular matrix")
    with pytest.raises(ValueError, match="Choose a"):
        read_ngspice_log_file(file)


def test_missing_file_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="not found"):
        read_ngspice_log_file(tmp_path / "missing.log")


def test_non_text_control_bytes_are_rejected(tmp_path):
    file = tmp_path / "control.log"
    file.write_bytes(b"Error\x07beep")
    with pytest.raises(ValueError, match="control bytes"):
        read_ngspice_log_file(file)


def fake_gui():
    gui = Mock()
    gui._is_generating = False
    gui._viewing_past_session = False
    gui.chat_history = []
    gui._last_image_paths = []
    return gui


def test_gui_import_passes_full_lines_to_existing_worker(tmp_path):
    from frontEnd import Chatbot as chat_ui
    file = tmp_path / "example.log"
    file.write_text("Warning: singular matrix\nWarning: floating pins\n")
    window = fake_gui()
    with patch.object(chat_ui.QFileDialog, "getOpenFileName", return_value=(str(file), "")):
        chat_ui.ChatbotGUI._import_ngspice_log(window)
    window._launch_text_worker.assert_called_once()
    history = window._launch_text_worker.call_args.args[0]
    assert history[-1] == "User: Analyze log: Warning: singular matrix\nWarning: floating pins\n"
    assert "example.log" in window._last_user_text
    window._start_thinking.assert_called_once()


def test_gui_cancel_does_not_start_worker():
    from frontEnd import Chatbot as chat_ui
    window = fake_gui()
    with patch.object(chat_ui.QFileDialog, "getOpenFileName", return_value=("", "")):
        chat_ui.ChatbotGUI._import_ngspice_log(window)
    window._launch_text_worker.assert_not_called()


def test_gui_bad_file_does_not_start_worker(tmp_path):
    from frontEnd import Chatbot as chat_ui
    file = tmp_path / "wrong.csv"
    file.write_text("Warning: singular matrix")
    window = fake_gui()
    with patch.object(chat_ui.QFileDialog, "getOpenFileName", return_value=(str(file), "")):
        chat_ui.ChatbotGUI._import_ngspice_log(window)
    window._launch_text_worker.assert_not_called()
    assert "Cannot import" in window.status_label.setText.call_args.args[0]


def test_gui_busy_does_not_open_file_picker():
    from frontEnd import Chatbot as chat_ui
    window = fake_gui()
    window._is_generating = True
    with patch.object(chat_ui.QFileDialog, "getOpenFileName") as picker:
        chat_ui.ChatbotGUI._import_ngspice_log(window)
    picker.assert_not_called()
    window._launch_text_worker.assert_not_called()

def test_windows_line_endings_are_normalized(tmp_path):
    file = tmp_path / "windows.log"
    file.write_bytes(b"Warning: singular matrix\r\nWarning: floating pins\r")
    assert read_ngspice_log_file(file) == (
        "Warning: singular matrix\nWarning: floating pins\n"
    )

def test_imported_log_reports_original_source_line_numbers(tmp_path):
    """Do not count the import command prefix as a log line."""
    from frontEnd import Chatbot as chat_ui
    from chatbot.chatbot_thread import _try_known_error_response

    log = tmp_path / "sample.log"
    log.write_text(
        "Warning: singular matrix\n"
        "Warning: floating pins\n"
        "Warning: singular matrix\n",
        encoding="utf-8",
    )
    window = fake_gui()
    with patch.object(
        chat_ui.QFileDialog, "getOpenFileName", return_value=(str(log), "")
    ):
        chat_ui.ChatbotGUI._import_ngspice_log(window)

    history = window._launch_text_worker.call_args.args[0]
    report = _try_known_error_response(history)
    assert report is not None
    assert "Occurrences: 2 | Source line(s): 1, 3" in report
    assert "Occurrences: 1 | Source line(s): 2" in report
