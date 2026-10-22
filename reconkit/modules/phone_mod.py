"""Native phone-number intelligence using the `phonenumbers` library.
Reimplements X-osint's phone feature (clean-room; no X-osint code)."""

from __future__ import annotations

from ..core.registry import register
from ..core.runner import timed, elapsed
from ..core.schema import ReconResult, Finding, TargetType


@register(
    name="phone",
    target_types=(TargetType.PHONE,),
    pymods=("phonenumbers",),
    install_hint="pip install phonenumbers",
)
def run(target: str) -> ReconResult:
    start = timed()
    res = ReconResult(module="phone", target=target, target_type=TargetType.PHONE)
    import phonenumbers
    from phonenumbers import carrier, geocoder, timezone

    try:
        # target should be E.164, e.g. +14155552671
        num = phonenumbers.parse(target, None)
    except phonenumbers.NumberParseException as e:
        res.ok, res.error = False, f"parse error: {e}"
        res.duration_s = elapsed(start)
        return res

    valid = phonenumbers.is_valid_number(num)
    res.findings.append(Finding("valid", str(valid), "phone"))
    res.findings.append(Finding("e164", phonenumbers.format_number(
        num, phonenumbers.PhoneNumberFormat.E164), "phone"))
    res.findings.append(Finding("region", geocoder.description_for_number(num, "en"), "phone"))
    car = carrier.name_for_number(num, "en")
    if car:
        res.findings.append(Finding("carrier", car, "phone"))
    tzs = timezone.time_zones_for_number(num)
    if tzs:
        res.findings.append(Finding("timezones", ", ".join(tzs), "phone"))
    res.findings.append(Finding("country_code", str(num.country_code), "phone"))
    res.duration_s = elapsed(start)
    return res
