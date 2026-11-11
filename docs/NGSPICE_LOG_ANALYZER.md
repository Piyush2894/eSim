# NgSpice Multi-error Log Analyzer (eSim AI Assistant)

## Purpose

The analyzer reuses eSim's predefined NgSpice error solutions to inspect
multiple diagnostic lines. It works **without Ollama**, is deterministic,
removes duplicate issue categories, ranks known severities and provides
recommended fixes with source line numbers. It is not a full SPICE parser or
substitute for reviewing the actual circuit.

## GUI usage (single-line input)

Enter a command such as:

```
Analyze log: Warning: singular matrix; Warning: floating pins
```

The semicolon separates log messages because the existing chat input is a
single-line field. A recognized issue can be handled offline. Unknown-only
inputs still require the normal AI runtime for general assistance.

## CLI usage (real multi-line file)

From the eSim repository root on Windows:

```
py src/chatbot/log_analyzer.py C:\path\to\simulation.log
```

Use UTF-8 text; undecodable bytes are replaced for robustness. No AI model is
required. The CLI is also useful for producing demonstration output.

## Architecture

- `src/chatbot/log_analyzer.py` contains model-free parsing and formatting.
- `src/chatbot/error_solutions.py` remains the source of known error definitions.
- `src/frontEnd/Chatbot.py` permits `Analyze log:` inputs offline when a
  recognized diagnostic exists.
- `src/chatbot/chatbot_thread.py` detects the command in `OllamaWorker` and
  returns the aggregated guidance through the existing Qt response signal.
- Normal Ollama streaming, image analysis and general queries retain their
  previous paths.

## Safety and limitations

- Recognizes **only** existing known rules; unknown lines are ignored.
- Truncates analysis at 200,000 characters and 4,000 source lines.
- Displays at most 25 unique issue categories.
- Does not prove whether suggested fixes will solve a particular circuit.
- Does not download or start Ollama for recognized log commands.
- GUI input accepts one line; use the CLI for full text logs.

## Tests

```
py -m pytest src/chatbot/tests/test_log_analyzer.py -v
```

Run the previously passing targeted eSim tests to detect regressions before
committing or pushing changes. Real GUI demonstration is a separate check.
