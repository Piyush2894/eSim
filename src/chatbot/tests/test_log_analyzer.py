"""Regression tests for model-free multi-error NgSpice log analysis."""

import sys
from pathlib import Path

src = Path(__file__).resolve().parents[2]
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

from chatbot.log_analyzer import analyze_ngspice_log, format_log_analysis


def test_two_distinct_known_errors():
    report = analyze_ngspice_log('Warning: singular matrix\nWarning: floating pins')
    descriptions = [item['description'] for item in report]
    assert len(descriptions) == 2
    assert len(set(descriptions)) == 2


def test_duplicate_error_is_grouped():
    report = analyze_ngspice_log('singular matrix\nFatal error: matrix is singular')
    assert len(report) == 1
    assert report[0]['count'] == 2
    assert report[0]['lines'] == [1, 2]


def test_critical_is_prioritized():
    report = analyze_ngspice_log('floating pins\nsingular matrix')
    assert len(report) == 2
    assert report[0]['severity'] == 'critical'
    assert report[1]['severity'] == 'moderate'


def test_unknown_only_has_no_findings():
    assert analyze_ngspice_log('unknown example diagnostic xyz') == []


def test_empty_or_invalid_input():
    assert analyze_ngspice_log('') == []
    assert analyze_ngspice_log(None) == []


def test_semicolon_single_line_log_for_gui():
    findings = analyze_ngspice_log('Warning: singular matrix; Warning: floating pins')
    assert len(findings) == 2
    assert [item['lines'] for item in findings] == [[1], [1]]


def test_formatted_report_contains_source_guidance():
    findings = analyze_ngspice_log('singular matrix')
    text = format_log_analysis(findings)
    assert 'recognized issue' in text
    assert 'Simulation convergence error' in text
    assert 'Recommended fixes' in text
    assert 'Source line' in text


def test_worker_log_route_needs_no_ollama():
    from chatbot.chatbot_thread import _try_known_error_response
    result = _try_known_error_response(['User: Analyze log: singular matrix; floating pins'])
    assert result is not None
    assert '2 recognized issues' in result
    assert 'Simulation convergence error' in result


def test_gui_offline_log_gate():
    from frontEnd.Chatbot import _can_answer_known_error_offline
    assert _can_answer_known_error_offline('Analyze log: singular matrix; floating pins')
    assert not _can_answer_known_error_offline('Analyze log: totally unfamiliar error xyz')
