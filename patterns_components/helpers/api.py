from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, date, timezone
from typing import Any, Callable

from dateutil import parser
from dateutil.parser import ParserError
from dcp.utils.common import utcnow
from requests import Request, Response, Session
from requests.auth import HTTPBasicAuth


### Rate-limiting and retry logic


def _parse_header_future_time_seconds(v: str | int | float) -> int | float | None:
    try:
        seconds = int(v)
        if seconds > 86400 * 365:
            # It's an epoch time, not a duration. So normalize to duration
            seconds = seconds - time.time()
        return seconds
    except (TypeError, ValueError):
        pass
    try:
        dt = parser.parse(v)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        seconds = max((dt - utcnow()).total_seconds(), 0)
        return seconds
    except ParserError:
        pass
    return None


def _icase_lookup(d: dict, k: str) -> Any:
    ld = {k.lower(): v for k, v in d.items()}
    return ld.get(k.lower())


@dataclass
class RateLimitHeaders:
    remaining_requests: int | None = None
    seconds_until_reset: int | None = None
    retry_after_seconds: int | None = None


def parse_rate_limit_headers(headers: dict) -> RateLimitHeaders:
    """Inspects default rate limit headers (e.g. X-RateLimit-*) for requests remaining and seconds to reset.

    Args:
        resp: requests library Response object

    Returns: RateLimitHeaders object with remaining_requests and seconds_until_reset attributes. Attribute is
        int if it was found on headers, otherwise None.
    """

    def get_ratelimit_header_value_fuzzy(headers: dict, key: str):
        for form in ["X-Rate-Limit-", "X-RateLimit-"]:
            v = _icase_lookup(headers, form + key)
            if v is not None:
                return v
        return None

    remaining = get_ratelimit_header_value_fuzzy(headers, "Remaining")
    reset = get_ratelimit_header_value_fuzzy(headers, "Reset")
    retry_after = _icase_lookup(headers, "Retry-After")
    headers = RateLimitHeaders()
    try:
        headers.remaining_requests = int(remaining)
    except (TypeError, ValueError):
        pass

    if reset is not None:
        headers.seconds_until_reset = _parse_header_future_time_seconds(reset)
    if retry_after is not None:
        headers.retry_after_seconds = _parse_header_future_time_seconds(retry_after)

    return headers


def handle_rate_limiting(
    resp: Response,
    retry_status_codes: list[int] = None,
    session: Session = None,
    backoff_sleep_seconds_if_no_headers: int = 5,
    max_backoff_attempts: int = 5,
    logger: Callable[[str], None] | None = print,
) -> Response:
    """Handles common rate-limiting and retry headers for a requests library Response object.

    Will retry requests with retryable status codes (429 and 503), using headers to wait
    appropriate amount of time or using exponential backoff if no headers present.

    Args:
        resp: requests Response object
        retry_status_codes: [429, 503] by default
        session: optional requests Session object, recommended for efficiency
        backoff_sleep_seconds_if_no_headers: starting seconds to sleep in backoff
        max_backoff_attempts: will abort after this many attempts

    Returns:

    """

    def _sleep(seconds: int, reason: str = ""):
        if logger:
            logger(f"Rate limited, sleeping for {seconds} seconds. ({reason})")
        time.sleep(seconds)

    def _retry_request(sess: Session):
        if logger:
            logger(f"Retrying request")
        return sess.send(resp.request)

    retry_status_codes = retry_status_codes or [429, 503]
    ratelimit_headers = parse_rate_limit_headers(resp.headers)
    if resp.status_code in retry_status_codes:
        # Display error to user
        try:
            logger(resp.json())
        except ValueError:
            logger(resp.text)
        if session is None:
            session = Session()
        buffer_seconds = 1
        if ratelimit_headers.retry_after_seconds:
            _sleep(
                ratelimit_headers.retry_after_seconds + buffer_seconds,
                "Retry-after header found",
            )
            return _retry_request(session)
        elif ratelimit_headers.seconds_until_reset:
            _sleep(
                ratelimit_headers.seconds_until_reset + buffer_seconds,
                "Rate-limit reset header found",
            )
            return _retry_request(session)
        else:
            sleep_seconds = backoff_sleep_seconds_if_no_headers
            for _ in range(max_backoff_attempts):
                _sleep(sleep_seconds, "Exp. backoff")
                resp = _retry_request(session)
                if resp.status_code in retry_status_codes:
                    sleep_seconds *= 2
                    continue
                return resp

    if (
        ratelimit_headers.remaining_requests == 0
        and ratelimit_headers.seconds_until_reset
    ):
        _sleep(ratelimit_headers.seconds_until_reset, "Rate-limit reset header found")
    return resp


### Authentication


def add_header_auth(
    req: Request, token: str, prefix: str = "Bearer", header: str = "Authorization"
):
    if prefix:
        token = f"{prefix} {token}"
    req.headers[header] = token


def add_basic_auth(req: Request, un: str, pw: str):
    req.auth = HTTPBasicAuth(un, pw)


### Misc


def clean_request_params(params: dict[str, Any], date_format="%F %T") -> dict[str, Any]:
    cleaned = {}
    for k, v in params.items():
        if isinstance(v, datetime) or isinstance(v, date):
            v = v.strftime(date_format)
        if v is None:
            continue
        cleaned[k] = v
    return cleaned


def raise_for_status_and_log(resp: Response):
    if not resp.ok:
        if "application/json" in resp.headers.get("Content-Type", ""):
            print(resp.json())
        else:
            print(resp.content)
        resp.raise_for_status()
