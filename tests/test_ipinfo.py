"""ipinfo: findings must match ip-api.com's own answer; the target must be
validated before it is put in the request URL."""

from __future__ import annotations

import json
import urllib.request

import pytest

from conftest import assert_clean_failure, labels_values
from reconkit.modules.ip_mod import _FIELDS


@pytest.mark.parametrize("target", [
    "999.1.1.1",
    "not an ip",
    "8.8.8.8/../../json/1.1.1.1",  # used to return 1.1.1.1's data as 8.8.8.8's
    "",
])
def test_invalid_ip_rejected_before_request(module, monkeypatch, target):
    def no_network(*a, **k):
        raise AssertionError("ipinfo made a request for an invalid IP")
    monkeypatch.setattr(urllib.request, "urlopen", no_network)
    assert_clean_failure(module("ipinfo").run(target), "not a valid IP address")


@pytest.mark.network
def test_matches_ip_api(module):
    r = module("ipinfo").run("8.8.8.8")
    assert r.ok, r.error

    url = f"http://ip-api.com/json/8.8.8.8?fields=status,message,{','.join(_FIELDS)}"
    with urllib.request.urlopen(url, timeout=15) as resp:
        raw = json.loads(resp.read())
    expected = {(k, str(raw[k])) for k in _FIELDS if raw.get(k) not in (None, "")}

    got = labels_values(r)
    assert got == expected
    assert ("country", "United States") in got
    assert "Google" in dict(got)["isp"]


@pytest.mark.network
def test_private_range(module):
    assert_clean_failure(module("ipinfo").run("10.0.0.1"), "private range")
