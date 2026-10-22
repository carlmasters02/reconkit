"""sherlock: every "[+] <Site>: <URL>" line, and nothing else, becomes a
Finding. fixtures/sherlock_output.txt was produced by sherlock 0.16.2's own
QueryNotifyPrint (as with --no-color, print_all on) for a made-up user, so it
also contains every non-hit line type the parser must ignore."""

from __future__ import annotations

import os
import shutil

import pytest

from conftest import labels_values
from reconkit.modules import sherlock_mod


def raw_hits(stdout: str) -> set[tuple[str, str]]:
    """Independent parse: split each [+] line at the first ': http'."""
    hits = set()
    for line in stdout.splitlines():
        if "[+]" in line:
            site, _, url = line.split("[+]", 1)[1].partition(": http")
            hits.add((site.strip(), "http" + url.strip()))
    return hits


def test_parses_fixture(module, replay):
    calls = replay(sherlock_mod, "sherlock_output.txt")
    r = module("sherlock").run("exampleuser")
    assert r.ok, r.error
    assert labels_values(r) == {
        ("GitHub", "https://www.github.com/exampleuser"),
        ("Reddit", "https://www.reddit.com/user/exampleuser"),
        ("Pinterest", "https://www.pinterest.com/exampleuser/"),
        ("Hacker News", "https://news.ycombinator.com/user?id=exampleuser"),
    }
    assert calls == [["sherlock", "exampleuser", "--print-found", "--no-color"]]


def test_missing_binary(module, monkeypatch, tmp_path):
    monkeypatch.setenv("PATH", str(tmp_path))  # empty dir: no CLI on PATH
    r = module("sherlock").run("exampleuser")
    assert r.ok is False and "binary not found" in r.error


@pytest.mark.live
@pytest.mark.skipif(not shutil.which("sherlock"), reason="sherlock not installed")
def test_live_matches_raw_output(module, record, tmp_path, monkeypatch):
    # octocat: GitHub's public demo account, so at least one hit is expected
    username = os.environ.get("RECONKIT_TEST_USERNAME", "octocat")
    monkeypatch.chdir(tmp_path)
    seen = record(sherlock_mod)

    r = module("sherlock").run(username)
    assert r.ok, r.error
    assert r.findings, "expected at least one account"
    assert labels_values(r) == raw_hits(seen["stdout"])
    assert list(tmp_path.iterdir()) == [], "sherlock left files in the cwd"
