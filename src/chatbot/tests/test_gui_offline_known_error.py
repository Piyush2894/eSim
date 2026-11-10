"""Regression checks for known-error help when Ollama is not installed."""
import sys
from pathlib import Path
from unittest.mock import Mock, patch

src_dir = Path(__file__).resolve().parents[2]
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from frontEnd import Chatbot as gui


def fake_window(text, model="No models found", attachments=None):
    window = Mock()
    window.user_input.text.return_value = text
    window.model_combo.currentText.return_value = model
    window._staged_images = attachments or []
    window._is_generating = False
    window._viewing_past_session = False
    window._editing_prompt_text = None
    window.chat_history = []
    window._last_image_paths = []
    return window


def test_offline_recognized_error_reaches_worker():
    window = fake_window("Warning: MATRIX IS SINGULAR")
    gui.ChatbotGUI.ask_ollama(window)
    window._launch_text_worker.assert_called_once()
    history = window._launch_text_worker.call_args.args[0]
    assert history[-1] == "User: Warning: MATRIX IS SINGULAR"


def test_offline_generic_query_is_rejected():
    window = fake_window("What is a capacitor?")
    gui.ChatbotGUI.ask_ollama(window)
    window._launch_text_worker.assert_not_called()
    assert "Ollama" in window.status_label.setText.call_args.args[0]


def test_offline_image_is_rejected():
    window = fake_window("Warning: MATRIX IS SINGULAR", attachments=["example.png"])
    gui.ChatbotGUI.ask_ollama(window)
    window._launch_vision_worker.assert_not_called()
    window._launch_text_worker.assert_not_called()
    assert "vision model" in window.status_label.setText.call_args.args[0]


def test_online_generic_query_still_reaches_worker():
    window = fake_window("What is a capacitor?", model="qwen2.5:3b")
    gui.ChatbotGUI.ask_ollama(window)
    window._launch_text_worker.assert_called_once()


def test_startup_keeps_input_enabled_during_model_check():
    window = Mock()
    with patch("chatbot.chatbot_thread.is_ollama_running", return_value=True):
        gui.ChatbotGUI._startup_check(window)
    window.user_input.setEnabled.assert_called_with(True)
    window.send_button.setEnabled.assert_called_with(True)

def test_failed_ollama_start_retains_offline_input():
    window = Mock()
    gui.ChatbotGUI._on_server_ready(window, False)
    window.user_input.setEnabled.assert_called_with(True)
    window.send_button.setEnabled.assert_called_with(True)
    assert "offline" in window.status_label.setText.call_args.args[0].lower()
