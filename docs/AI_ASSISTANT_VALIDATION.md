# eSim AI Assistant - Testing and Troubleshooting Guide

## Overview

This guide describes how to validate the eSim 2.6 AI Assistant's
error-classification component and Windows installer integration.

The AI Assistant uses Ollama for local model inference.
Some chatbot backend modules are not directly connected to the
user-facing chat panel.

## Requirements

For the targeted tests on Windows:

- Python
- pytest
- ollama Python package
- PyQt6

Install the required test dependencies:

    py -m pip install pytest ollama PyQt6

These Python packages alone do not install the Ollama server.

## 1. Error Classification Tests

Run from the eSim repository root:

    py -m pytest src/chatbot/tests/test_error_solutions.py src/chatbot/tests/test_error_solutions_regression.py -v

The regression tests verify:

- Recognition of "singular matrix"
- Recognition of warnings containing "singular matrix"
- Recognition of "matrix is singular"
- Case-insensitive matching
- Handling of None input
- Fallback for an unknown error

The word-order regression was reproduced before the fix:
4 passed, 2 failed.

After the fix, the targeted combined suite reported:
10 passed.

Note: Some older tests only print diagnostic failures and do
not assert every expected behavior. A pytest PASS for those
tests does not guarantee all diagnostic cases succeeded.

## 2. Windows AI Assistant Installer Tests

Run:

    py -m pytest windows/tests/test_ai_assistant.py -v

The test suite covers scenarios including:

- Optional installation task configuration
- Bundled Python and installer helper configuration
- Existing Ollama installation handling
- Download integrity verification
- Model download behavior
- Server startup and cleanup
- Handling download or installation errors

Local validation result:
15 passed.

Most installer interactions are simulated. One test exercises
downloading and SHA-256 verification using a local test server.
These tests do not replace an actual Windows installer test.

## 3. Combined Targeted Validation

Run:

    py -m pytest src/chatbot/tests/test_error_solutions.py src/chatbot/tests/test_error_solutions_regression.py windows/tests/test_ai_assistant.py -v

This combines the two previously validated test groups.

A successful run of these targeted tests does not establish
that the complete eSim application works end-to-end.

## 4. AI Assistant User Troubleshooting

If the AI Assistant does not appear in eSim:

1. Verify that the optional AI Assistant dependencies are installed.
2. Check whether the chatbot Python imports succeed.
3. Check the eSim application logs for startup errors.

If the AI Assistant cannot connect to its model:

1. Verify that Ollama is installed.
2. Confirm the Ollama server is running.
3. Check that the configured model is available.
4. Confirm the local Ollama endpoint is accessible.

The assistant normally communicates with Ollama at:

    http://localhost:11434

To inspect locally available models:

    ollama list

These troubleshooting checks are intended for installations
where the Ollama command-line program is available.

## 5. Limitations and Further Validation

Additional work is needed to validate:

- Complete GUI operation within eSim 2.6
- Netlist analysis from the project explorer
- Failed-simulation log explanations in the GUI
- Full Windows installer execution
- Ubuntu installer behavior
- Real local-model responses and error handling

The backend error-solution table is not currently invoked
directly by the standard user-facing chat panel.

## 6. Validation Record

Validation environment:
Windows, Python 3.14.5, pytest 9.2.0

Locally observed results:
- Error-classification tests: 10 passed
- Windows AI Assistant installer tests: 15 passed

Regression fix commit:
7a36cfed

This document describes targeted development validation,
not production certification or completed GUI integration.
