import time
from datetime import timedelta

import requests_mock
from dcp.utils.common import utcnow
from requests import Response, Request

from patterns_components.helpers.api import (
    handle_rate_limiting,
    RateLimitHeaders,
    parse_rate_limit_headers,
)


def test_parse_headers():
    # Parsing case
    assert parse_rate_limit_headers(
        {"X-RateLimit-Remaining": 0, "X-RateLimit-Reset": 1, "Retry-After": 2}
    ) == RateLimitHeaders(
        remaining_requests=0, seconds_until_reset=1, retry_after_seconds=2
    )
    assert parse_rate_limit_headers(
        {"x-rate-limit-remaining": 0, "x-rate-limit-reset": 1, "retry-after": 2}
    ) == RateLimitHeaders(
        remaining_requests=0, seconds_until_reset=1, retry_after_seconds=2
    )
    headers = parse_rate_limit_headers({"x-rate-limit-reset": 1970729917})
    assert headers.seconds_until_reset < 1800000000
    headers = parse_rate_limit_headers({"retry-after": "2030-01-01 00:00:00Z"})
    assert 0 < headers.retry_after_seconds < 1800000000
    headers = parse_rate_limit_headers({"retry-after": "2030-01-01 00:00:00"})
    assert 0 < headers.retry_after_seconds < 1800000000


test_url = "http://example.com"


def make_response(status_code, headers: dict = None, req: Request = None) -> Response:
    req = req or Request("GET", url=test_url)
    resp = Response()
    resp.headers = headers or {}
    resp.status_code = status_code
    resp.request = req.prepare()
    return resp


def test_rate_limiting_ok():
    resp = make_response(200)
    with requests_mock.Mocker() as m:
        m.get(test_url, json={"ok": True})
        handle_rate_limiting(resp)
        assert m.call_count == 0


def test_rate_limiting_no_headers():
    resp = make_response(429)
    start = time.monotonic()
    with requests_mock.Mocker() as m:
        m.get(test_url, json={"ok": True})
        handle_rate_limiting(resp, backoff_sleep_seconds_if_no_headers=1)
        assert m.call_count == 1
    # Should have waited one second
    assert time.monotonic() - start > 1


def test_rate_limiting_no_headers_503():
    resp = make_response(503)
    start = time.monotonic()
    with requests_mock.Mocker() as m:
        m.get(test_url, json={"ok": True})
        handle_rate_limiting(resp, backoff_sleep_seconds_if_no_headers=1)
        assert m.call_count == 1
    # Should have waited one second
    assert time.monotonic() - start > 1


def test_rate_limiting_none_remaining():
    resp = make_response(
        200, headers={"X-RateLimit-Remaining": 0, "X-RateLimit-Reset": 1}
    )
    start = time.monotonic()
    with requests_mock.Mocker() as m:
        m.get(test_url, json={"ok": True})
        handle_rate_limiting(resp)
        assert m.call_count == 0
    # Should have waited one second
    assert time.monotonic() - start > 1


def test_rate_limiting_retry_after():
    resp = make_response(
        429, headers={"Retry-After": (utcnow() + timedelta(seconds=1)).isoformat()}
    )
    start = time.monotonic()
    with requests_mock.Mocker() as m:
        m.get(test_url, json={"ok": True})
        handle_rate_limiting(resp)
        assert m.call_count == 1
    # Should have waited one second
    assert time.monotonic() - start > 1
