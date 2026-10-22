"""CLI: reports are well-formed and failed modules show their error."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from conftest import FIXTURES
from reconkit.cli import app

runner = CliRunner()


def flat(output: str) -> str:
    """Collapse whitespace so rich's line wrapping can't split a phrase."""
    return " ".join(output.split())


def test_json_and_md_reports(tmp_path):
    js, md = tmp_path / "r.json", tmp_path / "r.md"
    image = FIXTURES / "gps_paris.jpg"
    res = runner.invoke(app, ["run", str(image), "--type", "image",
                              "--json", str(js), "--md", str(md)])
    assert res.exit_code == 0, res.output

    data = json.loads(js.read_text())
    assert [r["module"] for r in data] == ["exif"]
    (r,) = data
    assert set(r) == {"module", "target", "target_type", "findings", "ok",
                      "error", "started_at", "duration_s"}
    assert r["ok"] is True and r["target_type"] == "image"
    assert len(r["findings"]) == 4
    for f in r["findings"]:
        assert set(f) == {"label", "value", "source", "extra"}
        assert f["source"] == "exif"

    lines = md.read_text().splitlines()
    assert lines[0] == f"# Recon report: `{image}`"
    assert lines[2].startswith("## ✅ exif (4 findings")
    finding_lines = [l for l in lines if l.startswith("- **")]
    assert len(finding_lines) == 4
    assert "- **maps**: https://maps.google.com/?q=48.85837,2.294481" in lines


def test_failed_module_shows_error():
    res = runner.invoke(app, ["run", "123", "--type", "phone"])
    assert res.exit_code == 0, res.output
    assert "phone: failed — not a valid phone number" in flat(res.output)


def test_error_text_is_not_eaten_as_markup(tmp_path):
    # exif on a directory fails with "[Errno 21] Is a directory"; unescaped,
    # rich would treat "[Errno 21]" as a markup tag and drop it
    res = runner.invoke(app, ["run", str(tmp_path), "--type", "image"])
    assert "exif: failed — cannot read EXIF: [Errno 21] Is a directory" in flat(res.output)


def test_unknown_target_type():
    res = runner.invoke(app, ["run", "x", "--type", "nope"])
    assert res.exit_code == 2
    assert "unknown target type" in flat(res.output)


def test_doctor_lists_all_modules():
    res = runner.invoke(app, ["doctor"])
    assert res.exit_code == 0
    for name in ["sherlock", "holehe", "subfinder", "theharvester",
                 "phone", "exif", "dns", "revdns", "ipinfo"]:
        assert name in res.output
