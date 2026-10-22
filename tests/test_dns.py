"""dns / revdns: lookups must match `dig`; bad input must fail cleanly."""

from __future__ import annotations

import pytest

from conftest import assert_clean_failure, dig


# --- offline: rejected before any lookup ---------------------------------

@pytest.mark.parametrize("name", ["a" * 64 + ".com", "bad..domain"])
def test_dns_malformed_name(module, name):
    # IDNA encoding fails (label too long / empty) — used to raise UnicodeError
    assert_clean_failure(module("dns").run(name), "resolution failed")


@pytest.mark.parametrize("ip", ["999.1.1.1", "not-an-ip", "", "8.8.8.8/24"])
def test_revdns_invalid_ip(module, ip):
    assert_clean_failure(module("revdns").run(ip), "not a valid IP address")


# --- network --------------------------------------------------------------

@pytest.mark.network
def test_dns_matches_dig(module):
    r = module("dns").run("example.com")
    assert r.ok, r.error
    got = {f.value for f in r.findings if f.label == "A"}
    assert got
    assert got == dig("A", "example.com")


@pytest.mark.network
@pytest.mark.parametrize("name", ["nonexistent-zz9x7q.invalid", ""])
def test_dns_unresolvable(module, name):
    assert_clean_failure(module("dns").run(name), "resolution failed")


@pytest.mark.network
def test_revdns_matches_dig(module):
    r = module("revdns").run("8.8.8.8")
    assert r.ok, r.error
    got = {f.value.rstrip(".") for f in r.findings}
    assert "dns.google" in got
    assert got == dig("-x", "8.8.8.8")


@pytest.mark.network
def test_revdns_no_ptr(module):
    # 192.0.2.0/24 is TEST-NET-1: valid address, no PTR record
    assert_clean_failure(module("revdns").run("192.0.2.1"), "reverse lookup failed")
