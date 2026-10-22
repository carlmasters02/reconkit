"""Shared fixtures and opt-in markers for the reconkit test suite.

By default only offline tests run. Opt in to the rest with:

    pytest --run-network   # DNS / ip-api lookups against stable public targets
    pytest --run-live      # real sherlock / holehe / subfinder / theHarvester runs
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

import reconkit.modules  # noqa: F401 — registers all modules
from reconkit.core import registry, runner

FIXTURES = Path(__file__).parent / "fixtures"


def pytest_addoption(parser):
    parser.addoption("--run-network", action="store_true",
                     help="run tests that make DNS / HTTP lookups")
    parser.addoption("--run-live", action="store_true",
                     help="run the external recon CLIs for real (slow, hits many sites)")


def pytest_collection_modifyitems(config, items):
    for marker, option in (("network", "--run-network"), ("live", "--run-live")):
        if config.getoption(option):
            continue
        skip = pytest.mark.skip(reason=f"needs {option}")
        for item in items:
            if marker in item.keywords:
                item.add_marker(skip)


@pytest.fixture
def module():
    """Look up a registered module by name: module("dns").run(target)."""
    def get(name: str):
        m = registry.get(name)
        assert m is not None, f"module {name!r} is not registered"
        return m
    return get


@pytest.fixture
def replay(monkeypatch):
    """Make a subprocess module see canned stdout instead of running its CLI.

    Returns the list of argv the module tried to run, for assertions.
    """
    calls: list[list[str]] = []

    def install(mod, fixture_name: str):
        text = (FIXTURES / fixture_name).read_text(encoding="utf-8")

        def fake_run_cmd(args, timeout=300):
            calls.append(args)
            return text, "", 0
        monkeypatch.setattr(mod, "run_cmd", fake_run_cmd)
        return calls
    return install


@pytest.fixture
def record(monkeypatch):
    """Run the real CLI but keep a copy of what the module saw, so a live
    run's findings can be checked against that exact raw output."""
    captured: dict = {}

    def install(mod):
        real = runner.run_cmd

        def recording_run_cmd(args, timeout=300):
            stdout, stderr, rc = real(args, timeout=timeout)
            captured.update(args=args, stdout=stdout, stderr=stderr, rc=rc)
            return stdout, stderr, rc
        monkeypatch.setattr(mod, "run_cmd", recording_run_cmd)
        return captured
    return install


def dig(*args: str) -> set[str]:
    """Answers from `dig +short`, trailing dots stripped."""
    if not shutil.which("dig"):
        pytest.skip("dig not installed")
    out = subprocess.run(["dig", "+short", *args], capture_output=True, text=True).stdout
    return {line.strip().rstrip(".") for line in out.splitlines() if line.strip()}


def labels_values(result) -> set[tuple[str, str]]:
    return {(f.label, f.value) for f in result.findings}


def assert_clean_failure(result, error_contains: str | None = None):
    """A failure must be ok=False with a message and no findings — not a crash."""
    assert result.ok is False
    assert result.error
    assert result.findings == []
    if error_contains:
        assert error_contains.lower() in result.error.lower()
