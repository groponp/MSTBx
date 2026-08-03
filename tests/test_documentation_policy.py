"""Regression tests for README language and documentation policy."""

from pathlib import Path


README = Path(__file__).parents[1] / "README.md"


def test_readme_declares_english_documentation_and_has_no_mixed_log_section():
    """The README stays English and does not expose implementation-only log policy."""
    text = README.read_text()

    assert "All README documentation must be written in English." in text
    assert "Logs de todas las herramientas" not in text
    assert "Todas las herramientas de MSTBx" not in text
