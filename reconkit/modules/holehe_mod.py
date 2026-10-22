"""Wrapper for holehe — checks which sites an email is registered on.
Upstream: https://github.com/megadose/holehe (GPL-3.0 — called as a separate
process, not imported, so reconkit stays MIT)."""

from __future__ import annotations

import re

from ..core.registry import register
from ..core.runner import run_cmd, timed, elapsed, ToolError
from ..core.schema import ReconResult, Finding, TargetType

# A hit is "[+] <domain>", optionally followed by recovery details
# ("j***@gmail.com / +1 ***42 / FullName ..."). The legend line "[+] Email
# used, [-] Email not used, [x] Rate limit" also starts with [+], so the
# first token must be a domain.
_HIT = re.compile(r"^\[\+\]\s+([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)(?:\s+(.*))?$")


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
        stdout, _, _ = run_cmd(
            ["holehe", "--only-used", "--no-color", "--no-clear", target], timeout=180)
    except ToolError as e:
        res.ok, res.error = False, str(e)
        res.duration_s = elapsed(start)
        return res
    for line in stdout.splitlines():
        m = _HIT.match(line.strip())
        if m:
            details = (m[2] or "").removeprefix("/").strip()
            extra = {"details": details} if details else {}
            res.findings.append(Finding(label="registered", value=m[1], source="holehe",
                                        extra=extra))
    res.duration_s = elapsed(start)
    return res
