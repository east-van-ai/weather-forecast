"""Pin the accepted command line.

A command line that drifts from the documented grammar still parses, it just
means something else, so nothing fails on its own when the surface moves.
These tests fail instead.
"""

import sys

import pytest

from weather_forecast import cli
from weather_forecast.args import EXIT_ARGPARSE, EXIT_ERROR, EXIT_OK, version_line


def invoke(monkeypatch, *tokens):
    """Run the tool with a command line and return its exit code.

    Codes arrive two ways: 0 and 1 return through main(), while argparse's 2
    and the version action's 0 unwind as a SystemExit. Both come back here as
    a number, so every test compares the same thing.
    """
    monkeypatch.setattr(sys, "argv", ["weather-forecast", *tokens])
    try:
        return cli.main()
    except SystemExit as stop:
        return stop.code


@pytest.fixture
def dispatched(monkeypatch):
    """Replace the run command with a recorder, and collect what it was given.

    The table binds cli_run.run at import, so patching that attribute would
    go unseen. The entry itself is replaced instead.
    """
    calls = []

    def fake_run(args):
        calls.append(args)
        return EXIT_OK

    monkeypatch.setitem(cli.COMMANDS, "run", fake_run)
    return calls


def test_bare_prints_the_banner(monkeypatch, capsys):
    """Test that a bare invocation answers with the banner, exit 0."""
    assert invoke(monkeypatch) == EXIT_OK
    printed = capsys.readouterr().out
    assert "weather-forecast" in printed
    assert "Usage:" in printed


def test_run_alone_prints_documentation(monkeypatch, capsys, dispatched):
    """Test that the run command word on its own answers with its own docs."""
    assert invoke(monkeypatch, "run") == EXIT_OK
    printed = capsys.readouterr().out
    assert "weather-forecast run" in printed
    assert "--commit" in printed
    assert dispatched == []


def test_run_without_a_mode_is_an_error(monkeypatch, capsys, dispatched):
    """Test that a run carrying no mode flag is our own error, exit 1."""
    assert invoke(monkeypatch, "run", "--force") == EXIT_ERROR
    printed = capsys.readouterr().err
    assert "--dry-run" in printed
    assert "Usage:" in printed
    assert dispatched == []


def test_run_dry_run(monkeypatch, dispatched):
    """Test that --dry-run reaches the run command."""
    assert invoke(monkeypatch, "run", "--dry-run") == EXIT_OK
    assert dispatched[0].dry_run is True
    assert dispatched[0].commit is False


def test_run_commit(monkeypatch, dispatched):
    """Test that --commit reaches the run command."""
    assert invoke(monkeypatch, "run", "--commit") == EXIT_OK
    assert dispatched[0].commit is True
    assert dispatched[0].force is False


def test_run_force_rides_a_mode(monkeypatch, dispatched):
    """Test that --force reaches the run command beside a mode flag."""
    assert invoke(monkeypatch, "run", "--commit", "--force") == EXIT_OK
    assert dispatched[0].commit is True
    assert dispatched[0].force is True


def test_run_mode_flags_conflict(monkeypatch, dispatched):
    """Test that the two mode flags together are argparse's error, exit 2."""
    assert invoke(monkeypatch, "run", "--dry-run", "--commit") == EXIT_ARGPARSE
    assert dispatched == []


def test_dryrun_spelling_is_retired(monkeypatch, dispatched):
    """Test that the old --dryrun spelling is an unknown flag, exit 2."""
    assert invoke(monkeypatch, "run", "--dryrun") == EXIT_ARGPARSE
    assert dispatched == []


def test_commit_is_not_abbreviated(monkeypatch, dispatched):
    """Test that a prefix of --commit is an unknown flag, exit 2."""
    assert invoke(monkeypatch, "run", "--com") == EXIT_ARGPARSE
    assert dispatched == []


def test_run_flag_is_retired(monkeypatch, dispatched):
    """Test that the old --run flag is an unknown flag, exit 2."""
    assert invoke(monkeypatch, "--run") == EXIT_ARGPARSE
    assert dispatched == []


def test_version_command(monkeypatch, capsys):
    """Test that the version command prints the version line, exit 0."""
    assert invoke(monkeypatch, "version") == EXIT_OK
    assert capsys.readouterr().out.strip() == version_line()


def test_version_flag(monkeypatch, capsys):
    """Test that --version prints the same line as the command, exit 0."""
    assert invoke(monkeypatch, "--version") == EXIT_OK
    assert capsys.readouterr().out.strip() == version_line()


def test_version_flag_is_not_a_command_option(monkeypatch, dispatched):
    """Test that asking run for the version is an unknown flag, exit 2."""
    assert invoke(monkeypatch, "run", "--version") == EXIT_ARGPARSE
    assert dispatched == []


def test_unknown_command(monkeypatch):
    """Test that an unknown command word is argparse's error, exit 2."""
    assert invoke(monkeypatch, "forecast") == EXIT_ARGPARSE


def test_flag_without_a_command(monkeypatch):
    """Test that a flag with no command word is argparse's error, exit 2."""
    assert invoke(monkeypatch, "--force") == EXIT_ARGPARSE


def test_stray_word_after_run(monkeypatch, capsys, dispatched):
    """Test that a bare word after run is named, with the usage line, exit 1."""
    assert invoke(monkeypatch, "run", "today") == EXIT_ERROR
    printed = capsys.readouterr().err
    assert "'today'" in printed
    assert "Usage:" in printed
    assert dispatched == []


def test_stray_word_after_a_flag(monkeypatch, dispatched):
    """Test that a bare word past the flags is caught too, exit 1."""
    assert invoke(monkeypatch, "run", "--commit", "today") == EXIT_ERROR
    assert dispatched == []


def test_stray_word_after_version(monkeypatch, capsys):
    """Test that the version command takes nothing after it, exit 1."""
    assert invoke(monkeypatch, "version", "today") == EXIT_ERROR
    assert "Usage:" in capsys.readouterr().err
