from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable, TypeVar, Generic

from patterns import *
from requests import Request, Session, Response, PreparedRequest


from .replication import (
    prepare_request_default,
    clean_request_params_default,
    handle_rate_limit_default,
    use_handle_retry_backoff,
    value_or_from_cfg,
)

C = TypeVar("C")
T = TypeVar("T")


@dataclass(frozen=True)
class EnricherContext(Generic[C]):
    input_store: Stream | Table
    output_store: Stream | Table
    state: State
    latest_request: Request | None = None
    latest_response: Response | None = None
    latest_input_records: list[dict] | None = None
    latest_output_records: list[dict] | None = None
    latest_error_records: list[dict] | None = None
    config: C | None = None
    iteration: int = -1
    latest_retry_count: int = 0
    error_store: Stream | Table | None = None


EnricherContextFunction = Callable[[EnricherContext[C]], T]


def handle_error_enrich_default(
    ctx: EnricherContext[C],
):
    # Errors specific to a single request
    request_specific_errors = [404, 422]
    # If not specific to a single request, raise the error
    if ctx.latest_response.status_code not in request_specific_errors:
        ctx.latest_response.raise_for_status()


def extract_error_records_default(ctx: EnricherContext) -> list[dict]:
    if ctx.latest_response.ok:
        return []
    error = {
        "status_code": ctx.latest_response.status_code,
        "response": ctx.latest_response.json(),
    }
    return [error]


def extract_single_record_handle_error_default(ctx: EnricherContext) -> list[dict]:
    if not ctx.latest_response or not ctx.latest_response.ok:
        return [None]
    return [ctx.latest_response.json()]


def use_merge_records(
    enrich_field_name: str = None,
    enrich_field_name_from_cfg_field: str = None,
    enrich_from_single_field: str = None,
    original_field_name: str = "record",
    original_field_name_from_cfg_field: str = None,
    method: str = "alongside",  # or "inject"
) -> EnricherContextFunction[list[dict]]:
    def merge_records(ctx: EnricherContext[C]) -> list[dict]:
        dest = value_or_from_cfg(
            ctx.config, enrich_field_name, enrich_field_name_from_cfg_field
        )
        orig = value_or_from_cfg(
            ctx.config, original_field_name, original_field_name_from_cfg_field
        )
        assert len(ctx.latest_input_records) == len(
            ctx.latest_output_records
        ), f"Mistmatched lengths {len(ctx.latest_input_records)} {len(ctx.latest_output_records)}"
        records = []
        for inr, outr in zip(ctx.latest_input_records, ctx.latest_output_records):
            if enrich_from_single_field and outr is not None:
                outr = outr.get(enrich_from_single_field)
            if method == "alongside":
                records.append(
                    {
                        orig: inr,
                        dest: outr,
                    }
                )
            elif method == "inject":
                inr[dest] = outr
                records.append(inr)
            else:
                Exception(f"Unsupported merge method {method}")
        return records

    return merge_records


def use_get_next_records_batch(
    batch_size: int = 1,
) -> EnricherContextFunction[list[dict]]:
    def get_next_records(ctx: EnricherContext[C]) -> list[dict]:
        records = []

        if hasattr(ctx.input_store, "consume_records"):
            consume = ctx.input_store.consume_records
        else:
            consume = ctx.input_store.as_stream().consume_records
        for r in consume():
            records.append(r)
            if len(records) == batch_size:
                break
        return records

    return get_next_records


def write_records_default(ctx: EnricherContext[C]):
    ctx.output_store.append(ctx.latest_output_records)


def write_error_records_default(ctx: EnricherContext[C]):
    if ctx.error_store and ctx.latest_error_records:
        ctx.error_store.append(ctx.latest_error_records)


### Template function


def enrich_records(
    input_store: Stream | Table,
    output_store: Stream | Table,
    state: State,
    config: C,
    build_request: EnricherContextFunction[Request | None],
    merge_records: EnricherContextFunction[list[dict]],
    get_next_records: EnricherContextFunction[
        list[dict] | None
    ] = use_get_next_records_batch(),
    extract_records: EnricherContextFunction[
        list[dict]
    ] = extract_single_record_handle_error_default,
    extract_error_records: EnricherContextFunction[
        list[dict]
    ] = extract_error_records_default,
    update_request_with_auth: EnricherContextFunction[None] | None = None,
    ratelimit_request: EnricherContextFunction[None] | None = handle_rate_limit_default,
    handle_retry: EnricherContextFunction[Request | None]
    | None = use_handle_retry_backoff(),
    handle_error: EnricherContextFunction[None] | None = handle_error_enrich_default,
    prepare_request: EnricherContextFunction[PreparedRequest] = prepare_request_default,
    clean_request_params: Callable[..., dict] = clean_request_params_default,
    write_records: EnricherContextFunction[None] = write_records_default,
    write_error_records: EnricherContextFunction[None] = write_error_records_default,
    handle_completion: EnricherContextFunction[None] = None,
    handle_incompletion: EnricherContextFunction[None] = None,
    session: Session = None,
    date_format: str = "%F %T",
    add_processed_at: bool = True,
    error_store: Stream | Table | None = None,
) -> bool:
    """
    enrich_records is a template function for enriching records in batches (a batch of one,
    by default) from a remote http API. It has function hooks for each stage of the process,
    and standard functions are provided for common use cases.

    All functions operate on a standard EnricherContext object that holds the current
    state and configuration for the import operation.

    Returns
        True if the enrich operation completed successfully (all input records enriched)
        and False otherwise
    """
    if add_processed_at:
        output_store.init(add_created="processed_at")
    base_ctx = EnricherContext(
        input_store=input_store,
        output_store=output_store,
        error_store=error_store,
        state=state,
        config=config,
    )
    ctx = replace(base_ctx)
    session = session or Session()

    completed_successfully = True
    iteration = 0

    while state.should_continue():
        # Ratelimit before continuing
        ratelimit_request(ctx)

        # Prepare a batch of records for enrichment
        input_records = get_next_records(ctx)
        if not input_records:
            break

        ctx = replace(base_ctx, latest_input_records=input_records, iteration=iteration)
        iteration += 1
        req = build_request(ctx)

        # New context for new cycle
        ctx = replace(ctx, latest_request=req)

        # Retry loop
        while ctx.latest_request is not None:
            # Prepare request
            if update_request_with_auth is not None:
                update_request_with_auth(ctx)
            ctx.latest_request.params = clean_request_params(
                ctx.latest_request.params, date_format=date_format
            )
            prepared_req = prepare_request(ctx.latest_request)

            # Send request
            print(f"{prepared_req.method} - {prepared_req.url}", end="")
            resp = session.send(prepared_req)
            print(f"Status {resp.status_code}")

            ctx = replace(
                ctx,
                latest_response=resp,
            )

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

        if extract_error_records:
            error_records = extract_error_records(ctx)
            ctx = replace(ctx, latest_error_records=error_records)

        records = extract_records(ctx)
        ctx = replace(ctx, latest_output_records=records)
        records = merge_records(ctx)
        ctx = replace(ctx, latest_output_records=records)

        if ctx.latest_output_records:
            write_records(ctx)
        if ctx.latest_error_records:
            write_error_records(ctx)

    else:
        state.request_new_run()
        completed_successfully = False

    if completed_successfully and handle_completion is not None:
        handle_completion(ctx)
    elif handle_incompletion is not None:
        handle_incompletion(ctx)

    return completed_successfully
