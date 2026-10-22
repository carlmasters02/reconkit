"""Unified result schema. Every module normalizes its output into ReconResult."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class TargetType(str, Enum):
    USERNAME = "username"
    EMAIL = "email"
    DOMAIN = "domain"
    PHONE = "phone"
    IP = "ip"
    IMAGE = "image"


@dataclass
class Finding:
    """One discovered artifact (a hit on a site, a subdomain, an email, etc.)."""
    label: str                       # e.g. "GitHub", "api.example.com"
    value: str                       # e.g. the URL, the subdomain, the email
    source: str                      # which module produced it
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReconResult:
    """Normalized output from a single module run."""
    module: str
    target: str
    target_type: TargetType
    findings: list[Finding] = field(default_factory=list)
    ok: bool = True
    error: str | None = None
    started_at: float = field(default_factory=time.time)
    duration_s: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["target_type"] = self.target_type.value
        return d


def dump_json(results: list[ReconResult]) -> str:
    return json.dumps([r.to_dict() for r in results], indent=2, default=str)


def dump_markdown(results: list[ReconResult], target: str) -> str:
    lines = [f"# Recon report: `{target}`", ""]
    for r in results:
        status = "✅" if r.ok else "❌"
        lines.append(f"## {status} {r.module} ({len(r.findings)} findings, {r.duration_s:.1f}s)")
        if r.error:
            lines.append(f"> error: {r.error}")
        for f in r.findings:
            lines.append(f"- **{f.label}**: {f.value}")
        lines.append("")
    return "\n".join(lines)
