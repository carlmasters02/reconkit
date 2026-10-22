"""subfinder / theHarvester: live checks run only when their CLIs are
installed; otherwise the wrapper must report "not installed" cleanly."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from reconkit.modules import subfinder_mod, theharvester_mod

HAS_SUBFINDER = shutil.which("subfinder") is not None
HAS_THEHARVESTER = shutil.which("theHarvester") is not None


@pytest.mark.parametrize("name, binary", [
    ("subfinder", "subfinder"),
    ("theharvester", "theHarvester"),
])
def test_not_installed_reports_cleanly(module, monkeypatch, tmp_path, name, binary):
    monkeypatch.setenv("PATH", str(tmp_path))  # empty dir: simulate no CLI
    m = module(name)
    assert m.installed is False
    r = m.run("example.com")
    assert r.ok is False
    assert r.error == f"binary not found: {binary}"
    assert r.findings == []


@pytest.mark.live
@pytest.mark.skipif(not HAS_SUBFINDER, reason="subfinder not installed")
def test_subfinder_live_matches_raw_output(module, record):
    seen = record(subfinder_mod)
    r = module("subfinder").run("example.com")
    assert r.ok, r.error
    raw = {line.strip() for line in seen["stdout"].splitlines() if line.strip()}
    assert {f.value for f in r.findings} == raw
    assert all(f.label == "subdomain" for f in r.findings)


@pytest.mark.live
@pytest.mark.skipif(not HAS_THEHARVESTER, reason="theHarvester not installed")
def test_theharvester_live_matches_raw_output(module, monkeypatch):
    # Copy theHarvester's JSON report out before the wrapper's tempdir is removed.
    seen = {}
    real = theharvester_mod.run_cmd

    def recording_run_cmd(args, timeout=300):
        out = real(args, timeout=timeout)
        report = Path(args[args.index("-f") + 1]).with_suffix(".json")
        seen["report"] = report.read_text() if report.exists() else None
        return out
    monkeypatch.setattr(theharvester_mod, "run_cmd", recording_run_cmd)

    r = module("theharvester").run("example.com")
    assert r.ok, r.error
    assert seen["report"] is not None, "theHarvester wrote no JSON report"
    data = json.loads(seen["report"])
    expected = ({("email", e) for e in data.get("emails", [])}
                | {("host", h) for h in data.get("hosts", [])})
    assert {(f.label, f.value) for f in r.findings} == expected
