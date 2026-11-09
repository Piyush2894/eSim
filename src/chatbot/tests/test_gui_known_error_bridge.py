"""Tests for GUI text worker and known-error backend integration."""

import sys
import types
from pathlib import Path
from unittest.mock import Mock, patch

src = Path(__file__).resolve().parents[2]
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

from chatbot import chatbot_thread as thread
from chatbot import error_solutions


def test_known_error_skips_ollama():
    worker = thread.OllamaWorker(
        ["User: matrix is singular"],
        model="qwen2.5:3b"
    )

    replies = []
    worker.response_signal.connect(replies.append)

    with patch.object(
        thread, "_try_known_error_response",
        return_value="Known error guidance"
    ), patch.object(
        thread, "_ensure_ollama_running"
    ) as server, patch.object(
        thread.ollama, "chat"
    ) as model:

        worker.run()

    assert replies == ["Known error guidance"]
    server.assert_not_called()
    model.assert_not_called()


def test_normal_message_still_streams():
    worker = thread.OllamaWorker(
        ["User: What is a resistor?"],
        model="qwen2.5:3b"
    )

    replies = []
    chunks = []

    worker.response_signal.connect(replies.append)
    worker.chunk_signal.connect(chunks.append)

    fake_stream = iter([
        {"message": {"content": "A "}},
        {"message": {"content": "resistor."}}
    ])

    with patch.object(
        thread, "_try_known_error_response",
        return_value=None
    ), patch.object(
        thread, "_ensure_ollama_running",
        return_value=True
    ), patch.object(
        thread.ollama, "chat",
        return_value=fake_stream
    ) as model:

        worker.run()

    assert replies == ["A resistor."]
    assert chunks == ["A ", "resistor."]
    assert model.call_args.kwargs["stream"] is True


def test_stopped_worker_does_not_emit_known_error():
    worker = thread.OllamaWorker(
        ["User: matrix is singular"]
    )

    replies = []
    worker.response_signal.connect(replies.append)

    worker.stop()

    with patch.object(
        thread, "_try_known_error_response",
        return_value="Known error"
    ), patch.object(
        thread, "_ensure_ollama_running"
    ) as server:

        worker.run()

    assert replies == []
    server.assert_not_called()


def test_bridge_calls_existing_backend():
    fake_core = types.ModuleType("chatbot.chatbot_core")

    fake_core.handle_esim_question = Mock(
        return_value="Backend troubleshooting answer"
    )

    solution = {
        "description": "Simulation convergence error",
        "severity": "critical",
        "fixes": ["Check circuit grounding"]
    }

    with patch.object(
        error_solutions, "get_error_solution",
        return_value=solution
    ), patch.dict(
        sys.modules,
        {"chatbot.chatbot_core": fake_core}
    ):

        reply = thread._try_known_error_response(
            ["User: matrix is singular"]
        )

    assert reply == "Backend troubleshooting answer"

    fake_core.handle_esim_question.assert_called_once_with(
        "matrix is singular", {}, None
    )


def test_unknown_error_returns_none():
    solution = {
        "description": "General schematic error",
        "severity": "unknown"
    }

    with patch.object(
        error_solutions, "get_error_solution",
        return_value=solution
    ):

        reply = thread._try_known_error_response(
            ["User: completely unknown issue xyz"]
        )

    assert reply is None


def test_real_error_lookup_without_optional_core():
    worker = thread.OllamaWorker(
        ["User: Fatal error: matrix is singular"],
        model="qwen2.5:3b"
    )

    replies = []
    worker.response_signal.connect(replies.append)

    # Use the real error dictionary while simulating
    # unavailable optional chatbot_core dependencies.
    with patch.dict(
        sys.modules,
        {"chatbot.chatbot_core": None}
    ), patch.object(
        thread, "_ensure_ollama_running"
    ) as server, patch.object(
        thread.ollama, "chat"
    ) as model:

        worker.run()

    assert len(replies) == 1
    assert "Simulation convergence error" in replies[0]
    assert "critical" in replies[0].lower()
    assert "Recommended fixes" in replies[0]

    server.assert_not_called()
    model.assert_not_called()
