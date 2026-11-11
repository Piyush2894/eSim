"""Regression tests for automatic NgSpice log routing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chatbot.chatbot_thread import _try_known_error_response


LOG = (
    "Warning: singular matrix\n"
    "Warning: floating pins\n"
    "Warning: singular matrix"
)

AUTO_PREFIX = "I got a simulation error. Here is the log:\n"


def test_automatic_failure_analyzes_all_errors():
    reply = _try_known_error_response(
        ["User: " + AUTO_PREFIX + LOG]
    )

    assert "NgSpice log analysis: 2 recognized issues" in reply
    assert "Simulation convergence error" in reply
    assert "Unconnected component pins" in reply
    assert "Occurrences: 2 | Source line(s): 1, 3" in reply
    assert "Occurrences: 1 | Source line(s): 2" in reply


def test_manual_import_unchanged():
    reply = _try_known_error_response(
        ["User: Analyze log:" + LOG]
    )

    assert "NgSpice log analysis: 2 recognized issues" in reply
    assert "Source line(s): 1, 3" in reply


def test_automatic_windows_newlines_preserve_line_numbers():
    reply = _try_known_error_response([
        "User: "
        + AUTO_PREFIX.replace("\n", "\r\n")
        + LOG.replace("\n", "\r\n")
    ])

    assert "Occurrences: 2 | Source line(s): 1, 3" in reply
    assert "Occurrences: 1 | Source line(s): 2" in reply


def test_normal_question_is_not_treated_as_simulation_log():
    reply = _try_known_error_response(
        ["User: What is a capacitor?"]
    )

    assert reply is None
