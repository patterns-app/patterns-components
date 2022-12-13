from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from patterns import Stream, State
from requests import Request

from patterns_components.helpers.replication import (
    use_extract_records_from_field,
    use_header_auth,
    use_update_state_latest_timestamp,
    DEFAULT_STATE_KEY,
    handle_retry_headers,
    use_handle_retry_backoff,
    ImporterContext,
    import_records,
    ImporterContextFunction,
    write_records_default,
)

api_url = "https://connect.squareup.com/v2/"
DEFAULT_MIN_DATE = datetime(2010, 1, 1)
date_format = "%FT%TZ"
cursor_state_key = "cursor"


def make_object_url(object_type: str) -> str:
    if object_type == "objects":
        object_type = "catalog/list"
    if object_type == "loyalty_accounts":
        object_type = "loyalty/accounts/search"
    return api_url + object_type


def make_state_key(location_id) -> str:
    state_key = f"{location_id}.latest_created_at"
    return state_key


@dataclass(frozen=True)
class SquareImporterConfig:
    access_token: str
    object_type: str
    state_key: str = DEFAULT_STATE_KEY
    request_params: dict = None


def square_get_next_request(
    ctx: ImporterContext[SquareImporterConfig],
) -> Request | None:
    params = {**(ctx.config.request_params or {})}
    if ctx.latest_response is not None:
        cursor = ctx.latest_response.json().get("cursor")
        if not cursor:
            # No more pages, we're all done, reset cursor for next run
            ctx.state.set_value(cursor_state_key, None)
            return None
        ctx.state.set_value(cursor_state_key, cursor)
    else:
        # Or cursor was saved in state from a previous run
        cursor = ctx.state.get_value(cursor_state_key)
    if cursor:
        params["cursor"] = cursor
    return Request(
        "GET",
        make_object_url(ctx.config.object_type),
        params=params,
    )


square_extract_records = use_extract_records_from_field(
    field_name_from_cfg_field="object_type"
)


square_update_request_with_auth = use_header_auth("access_token")


def handle_retry_bad_cursor(ctx: ImporterContext) -> Request | None:
    # Handle stale / bad cursor
    if ctx.latest_response is not None and ctx.latest_response.status_code == 400:
        if "cursor" in str(ctx.latest_response.json()):
            del ctx.latest_request.params["cursor"]
            print("Bad cursor. Removing and retrying.")
            return ctx.latest_request
    req = handle_retry_headers(ctx)
    if req:
        return req
    return use_handle_retry_backoff()(ctx)


def import_square_records(stream: Stream, state: State, cfg: SquareImporterConfig):
    finished = import_records(
        stream,
        state,
        cfg,
        get_next_request=square_get_next_request,
        extract_records=square_extract_records,
        update_request_with_auth=square_update_request_with_auth,
        date_format=date_format,
        handle_retry=handle_retry_bad_cursor,
    )
    if finished:
        # All done, reset cursor so we don't have a stale cursor next time
        state.set_value(cursor_state_key, None)


def import_square_records_update_state(
    stream: Stream,
    state: State,
    cfg: SquareImporterConfig,
    write_records: ImporterContextFunction[None] = write_records_default,
):
    update_state, update_request_with_state = use_update_state_latest_timestamp(
        "created_at",
        "begin_time",
        state_key=cfg.state_key,
        initial_timestamp=DEFAULT_MIN_DATE,
    )
    import_records(
        stream,
        state,
        cfg,
        get_next_request=square_get_next_request,
        extract_records=square_extract_records,
        update_request_with_auth=square_update_request_with_auth,
        update_state=update_state,
        update_request_with_state=update_request_with_state,
        date_format=date_format,
        write_records=write_records,
        handle_retry=handle_retry_bad_cursor,
    )
