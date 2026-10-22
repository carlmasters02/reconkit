"""Wrapper for theHarvester — emails, subdomains, hosts for a domain.
Upstream: https://github.com/laramies/theHarvester (GPL-2.0 — called as a
separate process, not imported)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ..core.registry import register
from ..core.runner import run_cmd, timed, elapsed, ToolError
from ..core.schema import ReconResult, Finding, TargetType


@register(
    name="theharvester",
    target_types=(TargetType.DOMAIN,),
    binary="theHarvester",
    install_hint="pipx install theHarvester",
)
def run(target: str) -> ReconResult:
    start = timed()
    res = ReconResult(module="theharvester", target=target, target_type=TargetType.DOMAIN)
    with tempfile.TemporaryDirectory() as tmp:
        stem = Path(tmp) / "out"
        try:
            run_cmd(
                ["theHarvester", "-d", target, "-b", "duckduckgo,crtsh,bing",
                 "-f", str(stem)],
                timeout=300,
            )
        except ToolError as e:
            res.ok, res.error = False, str(e)
            res.duration_s = elapsed(start)
            return res
        jf = stem.with_suffix(".json")
        if jf.exists():
            try:
                data = json.loads(jf.read_text(encoding="utf-8", errors="ignore"))
            except json.JSONDecodeError:
                data = {}
            for email in data.get("emails", []):
                res.findings.append(Finding(label="email", value=email, source="theharvester"))
            for host in data.get("hosts", []):
                res.findings.append(Finding(label="host", value=host, source="theharvester"))
    res.duration_s = elapsed(start)
    return res
