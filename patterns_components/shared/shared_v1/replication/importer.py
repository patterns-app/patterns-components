from __future__ import annotations

import os
import pprint
from dataclasses import dataclass, replace
from typing import Callable, TypeVar, Generic

from patterns import State, Table
from requests import Request, Session, Response, PreparedRequest

from .replication_helpers import (
    extract_records_json_default,
    handle_retry_headers,
    handle_error_raise_for_status,
    continue_if_any_records,
    prepare_request_default,
    clean_request_params_default,
    write_records_default,
    handle_rate_limit_default,
    use_handle_retry_backoff,
)

ENV = os.environ.get("ENVIRONMENT")
C = TypeVar("C")
T = TypeVar("T")


@dataclass(frozen=True)
class ImporterContext(Generic[C]):
    store: Table
    state: State
    latest_request: Request | None = None
    latest_response: Response | None = None
    latest_records: list[dict] | None = None
    config: C | None = None
    iteration: int = -1
    latest_retry_count: int = 0


ImporterContextFunction = Callable[[ImporterContext[C]], T]


def import_records(
    store: Table,
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
