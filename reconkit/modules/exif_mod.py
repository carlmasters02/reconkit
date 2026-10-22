"""Native EXIF + GPS metadata extraction from an image using Pillow.
Reimplements X-osint's image-metadata feature (clean-room)."""

from __future__ import annotations

from pathlib import Path

from ..core.registry import register
from ..core.runner import timed, elapsed
from ..core.schema import ReconResult, Finding, TargetType


def _to_deg(value, ref) -> float:
    d, m, s = (float(x) for x in value)
    dec = d + m / 60 + s / 3600
    if ref in ("S", "W"):
        dec = -dec
    return round(dec, 6)


@register(
    name="exif",
    target_types=(TargetType.IMAGE,),
    pymods=("PIL",),
    install_hint="pip install Pillow",
)
def run(target: str) -> ReconResult:
    start = timed()
    res = ReconResult(module="exif", target=target, target_type=TargetType.IMAGE)
    path = Path(target)
    if not path.exists():
        res.ok, res.error = False, f"file not found: {target}"
        res.duration_s = elapsed(start)
        return res

    from PIL import Image, ExifTags

    try:
        img = Image.open(path)
        exif = img._getexif() or {}
    except Exception as e:  # noqa: BLE001 — Pillow raises many types
        res.ok, res.error = False, f"cannot read EXIF: {e}"
        res.duration_s = elapsed(start)
        return res

    tagmap = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
    for key in ("Make", "Model", "DateTimeOriginal", "Software", "LensModel"):
        if key in tagmap:
            res.findings.append(Finding(key, str(tagmap[key]), "exif"))

    gps = tagmap.get("GPSInfo")
    if gps:
        g = {ExifTags.GPSTAGS.get(k, k): v for k, v in gps.items()}
        if {"GPSLatitude", "GPSLatitudeRef", "GPSLongitude", "GPSLongitudeRef"} <= g.keys():
            lat = _to_deg(g["GPSLatitude"], g["GPSLatitudeRef"])
            lon = _to_deg(g["GPSLongitude"], g["GPSLongitudeRef"])
            res.findings.append(Finding("gps", f"{lat}, {lon}", "exif"))
            res.findings.append(Finding(
                "maps", f"https://maps.google.com/?q={lat},{lon}", "exif"))

    if not res.findings:
        res.findings.append(Finding("note", "no EXIF/GPS metadata present", "exif"))
    res.duration_s = elapsed(start)
    return res
