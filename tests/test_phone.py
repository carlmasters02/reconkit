"""phone: findings must match what the phonenumbers library itself reports."""

from __future__ import annotations

import phonenumbers
import pytest
from phonenumbers import carrier, geocoder, timezone

from conftest import assert_clean_failure, labels_values


def expected_findings(number: str) -> set[tuple[str, str]]:
    """Independently derive the findings straight from phonenumbers."""
    try:
        n = phonenumbers.parse(number, None)
    except phonenumbers.NumberParseException:
        n = phonenumbers.parse(number, "US")
    exp = {
        ("valid", "True"),
        ("e164", phonenumbers.format_number(n, phonenumbers.PhoneNumberFormat.E164)),
        ("country_code", str(n.country_code)),
    }
    if region := geocoder.description_for_number(n, "en"):
        exp.add(("region", region))
    if car := carrier.name_for_number(n, "en"):
        exp.add(("carrier", car))
    if tzs := timezone.time_zones_for_number(n):
        exp.add(("timezones", ", ".join(tzs)))
    return exp


@pytest.mark.parametrize("number, e164, region", [
    ("+13529896238", "+13529896238", "Florida"),     # E.164
    ("352-989-6238", "+13529896238", "Florida"),     # US national format
    ("(352) 989-6238", "+13529896238", "Florida"),
    ("+442079460958", "+442079460958", "London"),    # non-US E.164
])
def test_valid_numbers(module, number, e164, region):
    r = module("phone").run(number)
    assert r.ok, r.error
    got = labels_values(r)
    assert got == expected_findings(number)
    assert ("e164", e164) in got
    assert ("region", region) in got
    assert all(f.value for f in r.findings), "no empty-valued findings"


@pytest.mark.parametrize("number, error", [
    ("not-a-number", "parse error"),
    ("", "parse error"),
    ("123", "not a valid phone number"),          # parses, but invalid
    ("+1 555 0100", "not a valid phone number"),
])
def test_invalid_numbers_fail_cleanly(module, number, error):
    assert_clean_failure(module("phone").run(number), error)
