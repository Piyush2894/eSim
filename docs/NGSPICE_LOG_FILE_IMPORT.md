# Import NgSpice simulation logs into the eSim AI Assistant

## User workflow

1. Open the eSim AI Assistant and click the **LOG** button beside the image attachment control.
2. Choose a `.log`, `.txt`, or `.out` file containing NgSpice messages.
3. The assistant routes the preserved multi-line contents to the existing
   deterministic NgSpice log analyzer. No Ollama model is required for known
   errors. Duplicate warnings are grouped, ordered by severity, and shown
   with guidance from eSim's existing error database.
4. General AI questions and unrecognized diagnostics still require the
   supported inference backend; the analyzer is not a full circuit diagnosis.

## Safety and limitations

- Local file selection only: no background scanning or upload.
- Maximum **128 KiB** and **4000 lines** to bound memory and UI work.
- UTF-8 (including BOM) and Windows-1252 logs are supported.
- Binary files, unsupported extensions, empty files, and oversized files are
  rejected with a status message.
- The selected log text is sent through the existing chat-history/worker
  pipeline, which stores chat sessions locally. Avoid importing secrets or
  confidential log contents until storage policy is reviewed.
- File line breaks are preserved so source-line references are meaningful.
- Full GUI and real Ollama integration require separate runtime checks.

## Tests

Run from the eSim repository root:

```powershell
py -m pytest src/chatbot/tests/test_log_file_import.py -v
```

Test file includes parser constraints, encoding, cancel/invalid/busy GUI
states, and worker handoff using the original file text.
