"""Wrapper for sherlock — username hunting across social networks.
Upstream: https://github.com/sherlock-project/sherlock (MIT)"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ..core.registry import register
from ..core.runner import run_cmd, timed, elapsed, ToolError
from ..core.schema import ReconResult, Finding, TargetType


@register(
    name="sherlock",
    target_types=(TargetType.USERNAME,),
    binary="sherlock",
    install_hint="pipx install sherlock-project",
)
def run(target: str) -> ReconResult:
    start = timed()
    res = ReconResult(module="sherlock", target=target, target_type=TargetType.USERNAME)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / f"{target}.json"
        try:
            # --nsfw off, JSON output, only print found
            run_cmd(["sherlock", target, "--output", str(out), "--print-found"], timeout=240)
        except ToolError as e:
            res.ok, res.error = False, str(e)
            res.duration_s = elapsed(start)
            return res
        # sherlock writes <username>.txt by default; parse the txt of found URLs
        txt = Path(tmp) / f"{target}.txt"
        if txt.exists():
            for line in txt.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if line.startswith("http"):
                    res.findings.append(Finding(label="account", value=line, source="sherlock"))
    res.duration_s = elapsed(start)
    return res
