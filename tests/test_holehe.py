"""holehe: only "[+] <domain>" hits become Findings — never the legend line
"[+] Email used, [-] Email not used, [x] Rate limit".

fixtures/holehe_output.txt is real holehe 1.61 output for test@example.com.
fixtures/holehe_output_details.txt was produced by holehe's own print_result
with hits that carry recovery email / phone / FullName details."""

from __future__ import annotations

import shutil

import pytest

from reconkit.modules import holehe_mod

REAL_HITS = {
    "any.do", "devrant.com", "eventbrite.com", "freelancer.com", "insightly.com",
    "lastpass.com", "office365.com", "plurk.com", "replit.com", "spotify.com",
    "teamtreehouse.com", "twitter.com", "xnxx.com", "xvideos.com",
}


def raw_hits(stdout: str) -> set[str]:
    """Independent parse: first token of each [+] line, minus the legend."""
    return {line.strip()[3:].split()[0] for line in stdout.splitlines()
            if line.strip().startswith("[+]") and "Email not used" not in line}


def test_real_output_excludes_legend(module, replay):
    calls = replay(holehe_mod, "holehe_output.txt")
    r = module("holehe").run("test@example.com")
    assert r.ok, r.error
    got = {f.value for f in r.findings}
    assert got == REAL_HITS
    assert all(f.label == "registered" for f in r.findings)
    assert not any("Email" in v for v in got)
    assert calls == [["holehe", "--only-used", "--no-color", "--no-clear",
                      "test@example.com"]]


def test_hits_with_recovery_details(module, replay):
    replay(holehe_mod, "holehe_output_details.txt")
    r = module("holehe").run("someone@example.com")
    assert r.ok, r.error
    assert {(f.value, f.extra.get("details", "")) for f in r.findings} == {
        ("amazon.com", "j****@gmail.com / +1 ******42"),
        ("github.com", ""),
        ("twitter.com", "+44 *******11"),          # phone only: leading "/ " dropped
        ("office365.com", "j****@outlook.com / FullName John Doe"),
    }


def test_missing_binary(module, monkeypatch, tmp_path):
    monkeypatch.setenv("PATH", str(tmp_path))  # empty dir: no CLI on PATH
    r = module("holehe").run("test@example.com")
    assert r.ok is False and "binary not found" in r.error


@pytest.mark.live
@pytest.mark.skipif(not shutil.which("holehe"), reason="holehe not installed")
def test_live_matches_raw_output(module, record):
    seen = record(holehe_mod)
    r = module("holehe").run("test@example.com")
    assert r.ok, r.error
    assert {f.value for f in r.findings} == raw_hits(seen["stdout"])
