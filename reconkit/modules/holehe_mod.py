"""Wrapper for holehe — checks which sites an email is registered on.
Upstream: https://github.com/megadose/holehe (GPL-3.0 — called as a separate
process, not imported, so reconkit stays MIT)."""

from __future__ import annotations

from ..core.registry import register
from ..core.runner import run_cmd, timed, elapsed, ToolError
from ..core.schema import ReconResult, Finding, TargetType


@register(
    name="holehe",
    target_types=(TargetType.EMAIL,),
    binary="holehe",
    install_hint="pipx install holehe",
)
def run(target: str) -> ReconResult:
    start = timed()
    res = ReconResult(module="holehe", target=target, target_type=TargetType.EMAIL)
    try:
        stdout, _, _ = run_cmd(["holehe", "--only-used", target], timeout=180)
    except ToolError as e:
        res.ok, res.error = False, str(e)
        res.duration_s = elapsed(start)
        return res
    for line in stdout.splitlines():
        line = line.strip()
        # holehe marks used accounts with a leading [+]
        if line.startswith("[+]"):
            site = line.removeprefix("[+]").strip()
            res.findings.append(Finding(label="registered", value=site, source="holehe"))
    res.duration_s = elapsed(start)
    return res
