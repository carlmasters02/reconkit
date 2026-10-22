"""Wrapper for subfinder — fast passive subdomain enumeration.
Upstream: https://github.com/projectdiscovery/subfinder (MIT)"""

from __future__ import annotations

from ..core.registry import register
from ..core.runner import run_cmd, timed, elapsed, ToolError
from ..core.schema import ReconResult, Finding, TargetType


@register(
    name="subfinder",
    target_types=(TargetType.DOMAIN,),
    binary="subfinder",
    install_hint="go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
)
def run(target: str) -> ReconResult:
    start = timed()
    res = ReconResult(module="subfinder", target=target, target_type=TargetType.DOMAIN)
    try:
        stdout, _, _ = run_cmd(["subfinder", "-d", target, "-silent"], timeout=300)
    except ToolError as e:
        res.ok, res.error = False, str(e)
        res.duration_s = elapsed(start)
        return res
    for line in stdout.splitlines():
        sub = line.strip()
        if sub:
            res.findings.append(Finding(label="subdomain", value=sub, source="subfinder"))
    res.duration_s = elapsed(start)
    return res
