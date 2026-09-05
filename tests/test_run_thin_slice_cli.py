import runpy
import sys

import pytest

from scripts.run_thin_slice import main


def _run(monkeypatch, argv_tail):
    monkeypatch.setattr(sys, "argv", ["run_thin_slice.py", *argv_tail])
    return main()


def test_default_args_exit_zero(monkeypatch, capsys):
    exit_code = _run(monkeypatch, [])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Generated 500 synthetic serving areas (seed=42)." in out


def test_explicit_count_and_seed_exit_zero(monkeypatch, capsys):
    exit_code = _run(monkeypatch, ["10", "7"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Generated 10 synthetic serving areas (seed=7)." in out


def test_zero_count_produces_concise_stderr_and_nonzero_exit(monkeypatch, capsys):
    exit_code = _run(monkeypatch, ["0", "42"])
    assert exit_code != 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "error:" in captured.err
    assert "Traceback" not in captured.err


def test_negative_count_produces_concise_stderr_and_nonzero_exit(monkeypatch, capsys):
    exit_code = _run(monkeypatch, ["-5", "42"])
    assert exit_code != 0
    captured = capsys.readouterr()
    assert "error:" in captured.err
    assert "Traceback" not in captured.err


def test_non_integer_count_produces_concise_stderr_and_nonzero_exit(monkeypatch, capsys):
    exit_code = _run(monkeypatch, ["abc", "42"])
    assert exit_code != 0
    captured = capsys.readouterr()
    assert "error:" in captured.err
    assert "Traceback" not in captured.err


def test_float_count_produces_concise_stderr_and_nonzero_exit(monkeypatch, capsys):
    exit_code = _run(monkeypatch, ["1.5", "42"])
    assert exit_code != 0
    captured = capsys.readouterr()
    assert "error:" in captured.err
    assert "Traceback" not in captured.err


def test_non_integer_seed_produces_concise_stderr_and_nonzero_exit(monkeypatch, capsys):
    exit_code = _run(monkeypatch, ["10", "seedy"])
    assert exit_code != 0
    captured = capsys.readouterr()
    assert "error:" in captured.err
    assert "Traceback" not in captured.err


def test_too_many_arguments_produces_concise_stderr_and_nonzero_exit(monkeypatch, capsys):
    exit_code = _run(monkeypatch, ["10", "42", "extra"])
    assert exit_code != 0
    captured = capsys.readouterr()
    assert "error:" in captured.err
    assert "Traceback" not in captured.err


def test_module_is_runnable_as_a_script_from_repo_root():
    # Regression test: `python scripts/run_thin_slice.py` must resolve the
    # `data_gen`/`risk` imports even though Python only puts the script's own
    # directory (not the repo root) on sys.path when run this way.
    module_globals = runpy.run_path(
        "scripts/run_thin_slice.py", run_name="__not_main__"
    )
    assert "generate_serving_areas" in module_globals
