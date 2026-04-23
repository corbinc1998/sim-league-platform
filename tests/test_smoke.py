"""Smoke tests proving the package imports and the test harness works."""

import pytest

from sim_league_platform import __version__, main


def test_package_has_version() -> None:
    """The package exposes a version string."""
    assert __version__ == "0.1.0"


def test_main_runs(capsys: pytest.CaptureFixture[str]) -> None:
    """The main entry point runs without error and prints the version."""
    main()
    captured = capsys.readouterr()
    assert "0.1.0" in captured.out
