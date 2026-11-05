
import sys
from pathlib import Path

import pytest

# Make the src directory importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chatbot.error_solutions import get_error_solution


@pytest.mark.parametrize("message", [
    "singular matrix",
    "Warning: singular matrix detected",
    "matrix is singular",
    "Warning: MATRIX IS SINGULAR",
])
def test_singular_matrix_variants(message):
    result = get_error_solution(message)

    assert result is not None
    assert result["severity"] == "critical"
    assert result["description"] == "Simulation convergence error"


def test_none_input():
    assert get_error_solution(None) is None


def test_unknown_error_fallback():
    result = get_error_solution("unrecognized circuit error xyz")

    assert result is not None
    assert result["severity"] == "unknown"
