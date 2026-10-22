"""Wrapper for sherlock — username hunting across social networks.
Upstream: https://github.com/sherlock-project/sherlock (MIT)"""

from __future__ import annotations

import re

from ..core.registry import register
from ..core.runner import run_cmd, timed, elapsed, ToolError
from ..core.schema import ReconResult, Finding, TargetType

# sherlock 0.16 prints each hit to stdout as "[+] <Site>: <URL>"
_HIT = re.compile(r"^\[\+\]\s+(.+?):\s+(https?://\S+)$")


@register(
    name="sherlock",
    target_types=(TargetType.USERNAME,),
    binary="sherlock",
    install_hint="pipx install sherlock-project",
)
def run(target: str) -> ReconResult:
    start = timed()
    res = ReconResult(module="sherlock", target=target, target_type=TargetType.USERNAME)
    try:
        # --nsfw off; no files written (0.16 only writes a txt with --txt)
        stdout, _, _ = run_cmd(
            ["sherlock", target, "--print-found", "--no-color"], timeout=240)
    except ToolError as e:
        res.ok, res.error = False, str(e)
        res.duration_s = elapsed(start)
        return res
    for line in stdout.splitlines():
        m = _HIT.match(line.strip())
        if m:
            res.findings.append(Finding(label=m[1], value=m[2], source="sherlock"))
    res.duration_s = elapsed(start)
    return res
