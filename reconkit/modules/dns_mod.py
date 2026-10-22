"""Native DNS lookup / reverse DNS using the standard library (no deps).
Reimplements X-osint's DNS lookup + reverse features (clean-room)."""

from __future__ import annotations

import socket

from ..core.registry import register
from ..core.runner import timed, elapsed
from ..core.schema import ReconResult, Finding, TargetType


@register(
    name="dns",
    target_types=(TargetType.DOMAIN,),
    pymods=(),  # stdlib only
    install_hint="",
)
def run(target: str) -> ReconResult:
    start = timed()
    res = ReconResult(module="dns", target=target, target_type=TargetType.DOMAIN)
    try:
        _, _, ips = socket.gethostbyname_ex(target)
        for ip in ips:
            res.findings.append(Finding("A", ip, "dns"))
    except socket.gaierror as e:
        res.ok, res.error = False, f"resolution failed: {e}"
    res.duration_s = elapsed(start)
    return res


@register(
    name="revdns",
    target_types=(TargetType.IP,),
    pymods=(),
    install_hint="",
)
def run_rev(target: str) -> ReconResult:
    start = timed()
    res = ReconResult(module="revdns", target=target, target_type=TargetType.IP)
    try:
        host, aliases, _ = socket.gethostbyaddr(target)
        res.findings.append(Finding("PTR", host, "revdns"))
        for a in aliases:
            res.findings.append(Finding("alias", a, "revdns"))
    except socket.herror as e:
        res.ok, res.error = False, f"reverse lookup failed: {e}"
    res.duration_s = elapsed(start)
    return res
