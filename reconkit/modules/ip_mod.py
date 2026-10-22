"""Native IP geolocation / info via the free ip-api.com endpoint (no key).
Reimplements X-osint's IP-info feature (clean-room)."""

from __future__ import annotations

import ipaddress
import json
import urllib.request

from ..core.registry import register
from ..core.runner import timed, elapsed
from ..core.schema import ReconResult, Finding, TargetType

_FIELDS = ("country", "regionName", "city", "isp", "org", "as", "lat", "lon", "timezone")


@register(
    name="ipinfo",
    target_types=(TargetType.IP,),
    pymods=(),  # stdlib urllib
    install_hint="",
)
def run(target: str) -> ReconResult:
    start = timed()
    res = ReconResult(module="ipinfo", target=target, target_type=TargetType.IP)
    # Validate before building the URL: a raw target like "8.8.8.8/../1.1.1.1"
    # would otherwise query a different IP and report it under this target.
    try:
        ip = ipaddress.ip_address(target.strip())
    except ValueError:
        res.ok, res.error = False, f"not a valid IP address: {target!r}"
        res.duration_s = elapsed(start)
        return res
    url = f"http://ip-api.com/json/{ip}?fields=status,message,{','.join(_FIELDS)}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:  # noqa: S310 — fixed host
            data = json.loads(resp.read().decode())
    except Exception as e:  # noqa: BLE001
        res.ok, res.error = False, f"lookup failed: {e}"
        res.duration_s = elapsed(start)
        return res

    if data.get("status") != "success":
        res.ok, res.error = False, data.get("message", "lookup failed")
        res.duration_s = elapsed(start)
        return res

    for f in _FIELDS:
        if data.get(f) not in (None, ""):
            res.findings.append(Finding(f, str(data[f]), "ipinfo"))
    res.duration_s = elapsed(start)
    return res
