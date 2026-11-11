"""Model-free analysis of multi-line NgSpice diagnostics.

Uses only the error definitions in error_solutions.py. Unknown diagnostics
are not assigned guessed explanations or severities. No Ollama, Qt, or RAG.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

if __package__:
    from .error_solutions import get_error_solution
else:
    from error_solutions import get_error_solution

MAX_LOG_CHARS = 200_000
MAX_LOG_LINES = 4_000
MAX_FINDINGS = 25

SEVERITY_RANK = {
    "critical": 0, "high": 1, "error": 2,
    "moderate": 3, "medium": 4, "warning": 5,
    "low": 6, "info": 7, "unknown": 8,
}


def _is_known_solution(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    description = str(value.get("description") or "").strip()
    severity = str(value.get("severity") or "unknown").lower().strip()
    return bool(description) and description.casefold() != "general schematic error" and severity != "unknown"


def analyze_ngspice_log(log_text: str) -> list[dict[str, Any]]:
    """Recognize, deduplicate, and rank errors in pasted or saved log text.

    Every finding includes description, severity, fixes, eSim action, count,
    line numbers, and the first matching input excerpt. Unrecognized lines are
    ignored. Semicolons may separate messages on one line for the GUI textbox.
    """
    if not isinstance(log_text, str) or not log_text.strip():
        return []

    # Bound work even if an accidentally huge file is passed in.
    lines = log_text[:MAX_LOG_CHARS].splitlines()[:MAX_LOG_LINES]
    grouped: dict[str, dict[str, Any]] = {}

    for number, original_line in enumerate(lines, 1):
        for segment in original_line.split(';'):
            line = segment.strip()
            if not line:
                continue
            # Error definitions come from the project, not inferred by an LLM.
            solution = get_error_solution(line[:1000])
            if not _is_known_solution(solution):
                continue

            description = str(solution['description']).strip()
            key = description.casefold()
            if key in grouped:
                grouped[key]['count'] += 1
                if number not in grouped[key]['lines']:
                    grouped[key]['lines'].append(number)
                continue
            if len(grouped) >= MAX_FINDINGS:
                continue

            fixes = solution.get('fixes') or []
            if isinstance(fixes, str):
                fixes = [fixes]
            grouped[key] = {
                'description': description,
                'severity': str(solution.get('severity') or 'unknown').lower(),
                'fixes': [str(fix) for fix in fixes if str(fix).strip()],
                'eSim_command': str(solution.get('eSim_command') or ''),
                'count': 1,
                'lines': [number],
                'example': line[:160],
            }

    return sorted(
        grouped.values(),
        key=lambda item: (
            SEVERITY_RANK.get(item['severity'], 8),
            item['lines'][0],
            item['description'].casefold(),
        ),
    )


def format_log_analysis(findings: list[dict[str, Any]]) -> str:
    """Create a readable GUI/terminal response for recognized findings."""
    if not findings:
        return (
            "No known NgSpice diagnostic patterns were found in this input. "
            "This is not proof that the circuit has no errors."
        )

    noun = 'issue' if len(findings) == 1 else 'issues'
    output = [f"**NgSpice log analysis: {len(findings)} recognized {noun}**"]
    for index, issue in enumerate(findings, 1):
        severity = issue['severity'].upper()
        output.append(f"\n**{index}. {issue['description']} ({severity})**")
        output.append(f"Occurrences: {issue['count']} | Source line(s): " +
                      ', '.join(map(str, issue['lines'][:15])))
        output.append('Example: ' + issue['example'].replace('`', "'"))
        if issue['fixes']:
            output.append('Recommended fixes:')
            output.extend(f"- {fix}" for fix in issue['fixes'])
        if issue['eSim_command']:
            output.append(f"eSim action: {issue['eSim_command']}")
    output.append('\nGuidance is based on recognized error patterns, not a full circuit diagnosis.')
    return '\n'.join(output)


def main() -> int:
    """CLI usage: py src/chatbot/log_analyzer.py C:/logs/ngspice.log"""
    import argparse

    parser = argparse.ArgumentParser(description='Analyze an NgSpice log using eSim known errors.')
    parser.add_argument('logfile', type=Path, help='Path to a plain-text simulation log')
    args = parser.parse_args()
    text = args.logfile.read_text(encoding='utf-8', errors='replace')
    print(format_log_analysis(analyze_ngspice_log(text)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
