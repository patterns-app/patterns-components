from __future__ import annotations

import os
import pprint
import time
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, date
from typing import Callable, TypeVar, Generic, Any, Tuple, Sequence

from dateutil.parser import parser, ParserError
from dcp.utils.common import utcnow, title_to_snake_case
from patterns import *
from requests import Request, Session, Response, PreparedRequest
from requests.auth import HTTPBasicAuth

ENV = os.environ.get("ENVIRONMENT")
C = TypeVar("C")
T = TypeVar("T")


@dataclass(frozen=True)
class ImporterContext(Generic[C]):
    store: Stream | Table
    state: State
    latest_request: Request | None = None
    latest_response: Response | None = None
    latest_records: list[dict] | None = None
    config: C | None = None
    iteration: int = -1
    latest_retry_count: int = 0


ImporterContextFunction = Callable[[ImporterContext[C]], T]


T = TypeVar("T")
DEFAULT_STATE_KEY = "importer_state"


def value_or_from_cfg(cfg: Any, val: T, from_cfg_field: str = None) -> T:
    if from_cfg_field:
        return getattr(cfg, from_cfg_field)
    return val


def continue_if_any_records(
    ctx: ImporterContext[C],
) -> bool:
    return bool(ctx.latest_records)


def handle_error_raise_for_status(
    ctx: ImporterContext[C],
):
    if ctx.latest_response is not None:
        if not ctx.latest_response.ok:
            print(ctx.latest_response.json())
        ctx.latest_response.raise_for_status()


def _parse_retry_after(retry_after: str) -> float | int | None:
    try:
        retry_seconds = int(retry_after)
        return retry_seconds
    except (TypeError, ValueError):
        pass
    try:
        dt = parser.parse(retry_after)
        seconds = (dt - utcnow()).total_seconds()
        return seconds
    except ParserError:
        pass
    return None


def get_retry_wait_seconds(resp: Response) -> int | None:
    retry_status_codes = [429, 503]
    if resp.status_code not in retry_status_codes:
        return None
    retry_after = resp.headers.get("Retry-After")
    if not retry_after:
        return None
    seconds = _parse_retry_after(retry_after)
    if seconds is None:
        return None
    max_sleep = 60 * 2  # 2 minutes is most we will sleep inside an execution
    seconds = min(max_sleep, max(0, seconds))
    return seconds


def handle_retry_headers(ctx: ImporterContext[C]) -> Request | None:
    if ctx.latest_response is None:
        return None
    seconds = get_retry_wait_seconds(ctx.latest_response)
    if not seconds:
        return None
    print(f"Rate limited, waiting {seconds} seconds for limit reset")
    time.sleep(seconds)
    return ctx.latest_request


def handle_rate_limit_default(ctx: ImporterContext[C]) -> Request | None:
    """
    Handles standard (somewhat) rate-limiting headers
    """

    def get_header_value(headers: dict, key: str):
        for form in ["X-Rate-Limit-", "X-RateLimit-"]:
            key = form + key.title()
            if key in headers:
                return headers[key]
            if key.lower() in headers:
                return headers[key.lower()]
        return None

    if not ctx.latest_request:
        return

    remaining = get_header_value(ctx.latest_request.headers, "remaining")
    reset = get_header_value(ctx.latest_request.headers, "reset")
    try:
        reset = int(reset)
    except (TypeError, ValueError):
        return
    try:
        remaining = int(remaining)
    except (TypeError, ValueError):
        return
    if remaining == 0:
        if (
            reset > 86400 * 365
        ):  # It's an epoch time, not a duration (APIs appear to use both ways)
            sleep_seconds = reset - time.time()
        else:
            sleep_seconds = reset
        if sleep_seconds > 60 * 5:
            raise Exception(
                f"Rate limited more than 5 minutes, aborting. ({ctx.latest_request.headers})"
            )
        print(f"Rate limited, waiting {sleep_seconds} seconds for limit reset")
        time.sleep(sleep_seconds + 1)  # Buffer by one


def write_records_default(ctx: ImporterContext[C]):
    ctx.store.append(ctx.latest_records)


def write_records_upsert(ctx: ImporterContext[C]):
    # TODO: replace this as default once we have transitioned all existing components to tables
    # attempt to upsert, if possible
    if hasattr(ctx.store, "upsert"):
        version = ctx.store.get_active_version()
        # TODO: remove this once schema cast mode is handled better (will currently throw exception for extra fields)
        if version.schema:
            records = []
            for r in ctx.latest_records:
                records.append(
                    {k: v for k, v in r.items() if k in version.schema.field_names()}
                )
        else:
            records = ctx.latest_records
        try:
            ctx.store.upsert(records)
            return
        except AssertionError:
            # Upsert throws an assertion error if unique is not defined
            print(
                "Attempted upsert, but schema does not exist or does not define `unique_on`. "
                "Records may be duplicated. Add an explicit schema or set in init "
                "`table.init(unique_on='my_id')`"
            )
    # otherwise:
    ctx.store.append(ctx.latest_records)


def extract_records_json_default(ctx: ImporterContext) -> list[dict]:
    return ctx.latest_response.json()


def use_handle_retry_backoff(
    exp: float = 1.5,
    multiplier: float = 2.0,
    constant: float = 1,
    retry_status_codes: list[int] = None,
):
    def handle_retry_backoff(ctx: ImporterContext[C]) -> Request | None:
        # First try looking for retry headers
        req = handle_retry_headers(ctx)
        if req:
            return req
        _retry_status_codes = retry_status_codes or [429, 503]
        if ctx.latest_response.status_code not in _retry_status_codes:
            return None
        sleep_seconds = (ctx.latest_retry_count + 1) ** exp * multiplier + constant
        print(f"Retrying in {sleep_seconds} seconds")
        time.sleep(sleep_seconds)
        return ctx.latest_request

    return handle_retry_backoff


def use_header_auth(
    cfg_field_name: str,
    header_name: str = "Authorization",
    prefix: str | None = "Bearer",
) -> ImporterContextFunction[None]:
    def add_auth(ctx: ImporterContext[C]):
        token = getattr(ctx.config, cfg_field_name)
        if prefix:
            token = f"{prefix} {token}"
        ctx.latest_request.headers[header_name] = token

    return add_auth


def use_basic_auth(
    cfg_username_name: str = "username",
    cfg_password_name: str = "password",
) -> ImporterContextFunction[None]:
    def add_auth(ctx: ImporterContext[C]):
        un = getattr(ctx.config, cfg_username_name, "")
        pw = getattr(ctx.config, cfg_password_name, "")
        ctx.latest_request.auth = HTTPBasicAuth(un, pw)

    return add_auth


def use_update_state_with_latest_value(
    record_field: str,
    request_parameter_name: str = None,
    state_key: str = DEFAULT_STATE_KEY,
    ascending: bool = True,
    records_are_sorted: bool = True,
    initial_value: Any = None,
    initial_value_cfg_field: str = None,
    update_request: Callable[[Request, Any], None] = None,
    state_key_suffix_from_cfg_field: str = None,
) -> Tuple[ImporterContextFunction[None], ImporterContextFunction[None]]:
    def get_state_key(cfg: C):
        suffix = ""
        if state_key_suffix_from_cfg_field:
            suffix = "_" + getattr(cfg, state_key_suffix_from_cfg_field)
        return state_key + suffix

    def update_state(ctx: ImporterContext[C]):
        _state_key = get_state_key(ctx.config)
        if not ctx.latest_records:
            return
        extreme_value = None
        if records_are_sorted:
            extreme_value = ctx.latest_records[-1][record_field]
        else:
            for r in ctx.latest_records:
                val = r[record_field]
                if extreme_value is None or (
                    val > extreme_value if ascending else val < extreme_value
                ):
                    extreme_value = val
        ctx.state.set_value(_state_key, extreme_value)

    def update_request_with_state(ctx: ImporterContext[C]) -> None:
        _state_key = get_state_key(ctx.config)
        initial_v = value_or_from_cfg(
            ctx.config, initial_value, initial_value_cfg_field
        )
        v = ctx.state.get_value(_state_key, initial_v)
        if v is not None:
            if update_request is not None:
                update_request(ctx.latest_request, v)
            elif request_parameter_name is not None:
                ctx.latest_request.params.update({request_parameter_name: v})
            else:
                raise Exception(
                    "Must specify one of request_parameter_name or update_request"
                )

    return update_state, update_request_with_state


def use_update_state_latest_timestamp(
    timestamp_field: str,
    request_parameter_name: str = None,
    state_key: str = DEFAULT_STATE_KEY,
    ascending: bool = True,
    records_are_sorted: bool = True,
    initial_timestamp: datetime = None,
    buffer_interval: timedelta = None,
    initial_timestamp_cfg_field: str = None,
    buffer_interval_cfg_field: str = None,
    update_request: Callable[[Request, Any], None] = None,
    update_only_first_request: bool = False,  # if subsequent requests are paginated
    state_key_suffix_from_cfg_field: str = None,
) -> Tuple[ImporterContextFunction[None], ImporterContextFunction[None]]:
    def get_state_key(cfg: C):
        suffix = ""
        if state_key_suffix_from_cfg_field:
            suffix = "_" + getattr(cfg, state_key_suffix_from_cfg_field)
        return state_key + suffix

    def update_state(ctx: ImporterContext[C]):
        _state_key = get_state_key(ctx.config)
        if not ctx.latest_records:
            return
        extreme_value = None
        if records_are_sorted:
            extreme_value = ctx.latest_records[-1][timestamp_field]
        else:
            for r in ctx.latest_records:
                val = r[timestamp_field]
                if extreme_value is None or (
                    val > extreme_value if ascending else val < extreme_value
                ):
                    extreme_value = val
        ctx.state.set_value(_state_key, extreme_value)

    def update_request_with_state(ctx: ImporterContext[C]) -> None:
        _state_key = get_state_key(ctx.config)
        if update_only_first_request:
            if ctx.iteration > 0:
                return
        initial_ts = value_or_from_cfg(
            ctx.config, initial_timestamp, initial_timestamp_cfg_field
        )
        dt = ctx.state.get_datetime(_state_key)
        if dt is None:
            # Use initial ts
            dt = initial_ts
        else:
            # Compute buffer (but only if NOT using initial_ts)
            buffer = value_or_from_cfg(
                ctx.config, buffer_interval, buffer_interval_cfg_field
            )
            if isinstance(buffer, int):
                buffer = timedelta(seconds=buffer)
            if buffer:
                dt -= buffer

        if dt is not None:
            if update_request is not None:
                update_request(ctx.latest_request, dt)
            elif request_parameter_name is not None:
                ctx.latest_request.params.update({request_parameter_name: dt})
            else:
                raise Exception(
                    "Must specify one of request_parameter_name or update_request"
                )

    return update_state, update_request_with_state


def use_handle_retry_wait_on_status_codes(
    status_codes: list[int], seconds_to_wait: int
) -> ImporterContextFunction[Request | None]:
    def handle_retry(ctx: ImporterContext[C]) -> Request | None:
        if ctx.latest_response and ctx.latest_response.status_code in status_codes:
            time.sleep(seconds_to_wait)
            return ctx.latest_request
        return None

    return handle_retry


def transform_keys_snake_case(r: dict) -> dict:
    return {title_to_snake_case(k): v for k, v in r.items()}


def use_extract_records_from_field(
    field_name: str = None,
    field_name_from_cfg_field: str = None,
    snake_case_keys: bool = False,
) -> ImporterContextFunction[list[dict]]:
    def extract_records(ctx: ImporterContext[C]) -> list[dict]:
        fname = value_or_from_cfg(ctx.config, field_name, field_name_from_cfg_field)
        if fname is None:
            raise Exception(
                "Must specify one of field_name or field_name_from_cfg_field"
            )
        records = ctx.latest_response.json().get(fname, [])
        if snake_case_keys:
            records = [transform_keys_snake_case(r) for r in records]
        return records

    return extract_records


def clean_request_params_default(params: dict, date_format="%F %T") -> dict:
    cleaned = {}
    for k, v in params.items():
        if isinstance(v, datetime) or isinstance(v, date):
            v = v.strftime(date_format)
        if v is None:
            continue
        cleaned[k] = v
    return cleaned


def prepare_request_default(req: Request) -> PreparedRequest:
    return req.prepare()


### Replication manager


@dataclass
class ObjectImporter:
    key: str
    import_records: Callable[[bool], bool]


def handle_exception(state: State, importer: ObjectImporter, e: Exception):
    if any([m in str(e).lower() for m in ["internal error", "rate limit"]]):
        # If temp error run again in a couple minutes
        state.request_new_run(wait_atleast_seconds=120)
    raise e


def full_replication_manager(
    state: State,
    importers: list[ObjectImporter] | list[Sequence[str, Callable[[bool], bool]]],
    min_wait_after_successful_completion_seconds: int = 60 * 30,
):
    """Helps manage multiple importers in single node"""

    importers = [
        i if isinstance(i, ObjectImporter) else ObjectImporter(*i) for i in importers
    ]

    def get_state_key(importer_key: str, s: str) -> str:
        return f"replication_state_{importer_key}_last_{s}"

    def get_importer_state(importer: ObjectImporter) -> dict:
        return {
            "exe_start_at": state.get_datetime(
                get_state_key(importer.key, "exe_start_at")
            ),
            "exe_done_at": state.get_datetime(
                get_state_key(importer.key, "exe_done_at")
            ),
            "exe_status": state.get_value(get_state_key(importer.key, "exe_status")),
        }

    def set_importer_state(importer: ObjectImporter, istate: dict):
        for k, v in istate.items():
            state.set_value(get_state_key(importer.key, k), v)

    def run_importer(
        importer: ObjectImporter, istate: dict, backfill: bool = False
    ) -> bool:
        print(f"Replicating {importer.key}")
        istate["exe_start_at"] = utcnow()
        set_importer_state(importer, istate)

        try:
            success = importer.import_records(backfill)
        except Exception as e:
            istate["exe_status"] = "error"
            set_importer_state(importer, istate)
            handle_exception(state, importer, e)

        istate["exe_status"] = "success" if success else "incomplete"
        istate["exe_done_at"] = utcnow()
        set_importer_state(importer, istate)
        if not success:
            # We timed out, exit
            exit()
        return success

    # first run any that have never attempted
    for importer in importers:
        istate = get_importer_state(importer)
        if istate["exe_start_at"]:
            continue
        run_importer(importer, istate, backfill=True)

    # Next run incompletes
    for importer in importers:
        istate = get_importer_state(importer)
        if istate["exe_status"] != "incomplete":
            continue
        run_importer(importer, istate, backfill=True)

    # Next run things that had success before
    for importer in importers:
        istate = get_importer_state(importer)
        if istate["exe_status"] != "success":
            continue
        if (
            utcnow() - istate["exe_done_at"]
        ).total_seconds() < min_wait_after_successful_completion_seconds:
            continue
        run_importer(importer, istate)

    # Finally run previous errors (they may error again, so run last to allow others chance to run)
    # TODO: more robust to multiple failing importers
    for importer in importers:
        istate = get_importer_state(importer)
        if istate["exe_status"] != "error":
            continue
        run_importer(
            importer, istate, backfill=True
        )  # TODO: backfill true? in practice makes sense, but weird)


### Template function


def import_records(
    store: Stream | Table,
    state: State,
    config: C,
    get_next_request: ImporterContextFunction[Request | None],
    extract_records: ImporterContextFunction[list[dict]] = extract_records_json_default,
    update_request_with_auth: ImporterContextFunction[None] | None = None,
    update_request_with_state: ImporterContextFunction[None] | None = None,
    update_state: ImporterContextFunction[None] | None = None,
    ratelimit_request: ImporterContextFunction[None] | None = handle_rate_limit_default,
    handle_retry: ImporterContextFunction[Request | None]
    | None = use_handle_retry_backoff(),
    handle_error: ImporterContextFunction[None] | None = handle_error_raise_for_status,
    check_should_continue: ImporterContextFunction[bool]
    | None = continue_if_any_records,
    prepare_request: ImporterContextFunction[PreparedRequest] = prepare_request_default,
    clean_request_params: Callable[..., dict] = clean_request_params_default,
    write_records: ImporterContextFunction[None] = write_records_default,
    handle_completion: ImporterContextFunction[None] = None,
    handle_incompletion: ImporterContextFunction[None] = None,
    session: Session = None,
    date_format: str = "%F %T",
) -> bool:
    """
    import_records is a template function for incrementally importing records
    from a remote http API. It has function hooks for each stage of the process,
    and standard functions are provided for common use cases.

    All functions operate on a standard ImporterContext object that holds the current
    state and configuration for the import operation.

    Returns: True if the import operation completed successfully (all records imported from
    remote API) and False otherwise (eg some but not all records imported or an error was encountered)
    """
    base_ctx = ImporterContext(store=store, state=state, config=config)
    ctx = replace(base_ctx)
    session = session or Session()

    completed_successfully = True
    iteration = 0

    # Loop until protocol times us out
    while state.should_continue():
        # Ratelimit before continuing
        ratelimit_request(ctx)

        req = get_next_request(ctx)

        # If no next request, we're done
        if req is None:
            break

        # New context for new cycle
        ctx = replace(base_ctx, latest_request=req, iteration=iteration)
        iteration += 1

        # Retry loop
        while True:
            # Prepare request
            if update_request_with_auth is not None:
                update_request_with_auth(ctx)
            if update_request_with_state is not None:
                update_request_with_state(ctx)
            ctx.latest_request.params = clean_request_params(
                ctx.latest_request.params, date_format=date_format
            )
            prepared_req = prepare_request(ctx.latest_request)

            # Send request
            print(f"{prepared_req.method} - {prepared_req.url}")
            if ENV == "staging" and ctx.latest_request.json:
                print(pprint.pformat(ctx.latest_request.json))
            resp = session.send(prepared_req)
            print(f"Status {resp.status_code}")
            ctx = replace(ctx, latest_response=resp)

            retry_req = handle_retry(ctx) if handle_retry is not None else None
            if retry_req is None:
                break
            # If retry request is not none, then retry with new request
            ctx = replace(
                ctx,
                latest_request=retry_req,
                latest_retry_count=ctx.latest_retry_count + 1,
            )

        # Handle error (Should raise exception if unrecoverable error,
        # recoverable errors should be handled in handle_retry)
        if handle_error is not None:
            handle_error(ctx)

        records = extract_records(ctx)
        ctx = replace(ctx, latest_records=records)

        if ctx.latest_records:
            write_records(ctx)

        if update_state is not None:
            update_state(ctx)

        if check_should_continue is not None and not check_should_continue(ctx):
            break
    else:
        state.request_new_run()
        completed_successfully = False

    if completed_successfully and handle_completion is not None:
        handle_completion(ctx)
    elif handle_incompletion is not None:
        handle_incompletion(ctx)

    return completed_successfully
