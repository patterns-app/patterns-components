from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import timedelta, datetime
from typing import Tuple

from dcp.utils.common import utcnow
from patterns import Stream, State, Table
from requests import Request

from patterns_components.helpers.replication import (
    ImporterContext,
    import_records,
    ImporterContextFunction,
    use_basic_auth,
    use_extract_records_from_field,
    use_update_state_with_latest_value,
    write_records_upsert,
)

"""
N.B.

The Stripe API returns records only in order by `created desc`. This means
replicating involves the following steps:
    * if no successful complete backfill yet, fetch records for all time, backwards:
        * fetch backwards using the object id and `starting_after` param, saving progress
        of id to state as we go.
        * once we have exhausted this backfill, clear the `starting_after` state and mark
        the `latest_successful_completion` state at the current time.
    * for future runs, fetch backwards for `curing_window_days` number of days, looking
    for new records and updates to existing records in same manner as original backfill, but
    limiting to curing window using created filters.
"""

STRIPE_API_BASE_URL = "https://api.stripe.com/v1/"


def latest_full_import_state_key(object_type: str) -> str:
    return f"latest_full_import_at__{object_type}"


def current_starting_after_state_key(object_type: str) -> str:
    return f"current_starting_after__{object_type}"


@dataclass(frozen=True)
class StripeImporterConfig:
    api_key: str
    curing_window_days: int
    object_type: str
    request_params: dict = None
    secondary_store: Table = None
    start_date: datetime = None


def make_object_url(object_type: str) -> str:
    return STRIPE_API_BASE_URL + object_type


non_filterable_object_types = [
    "subscription_items",
]


def stripe_get_next_request(
    ctx: ImporterContext[StripeImporterConfig],
) -> Request | None:
    params = {"limit": 100, **(ctx.config.request_params or {})}
    url = make_object_url(ctx.config.object_type)
    if ctx.latest_response is not None:
        if not ctx.latest_response.json().get("has_more"):
            # All done
            return None

    # Only filter created on endpoints that allow it
    if ctx.config.object_type not in non_filterable_object_types:
        latest_full_import_at = ctx.state.get_datetime(
            latest_full_import_state_key(ctx.config.object_type)
        )
        if latest_full_import_at:
            # Import only more recent than latest imported at date, offset by a curing window
            # (default 90 days) to capture updates to objects
            # (Stripe only allows sorting on created_at, so we have to check back in time for record updates)
            params["created[gte]"] = int(
                (
                    latest_full_import_at
                    - timedelta(days=int(ctx.config.curing_window_days))
                ).timestamp()
            )
        elif ctx.config.start_date:
            params["created[gte]"] = int(ctx.config.start_date.timestamp())
    return Request(
        "GET",
        url,
        params=params,
    )


stripe_update_request_with_auth = use_basic_auth("api_key")


def stripe_use_update_state(
    cfg: StripeImporterConfig,
) -> Tuple[ImporterContextFunction[None], ImporterContextFunction[None]]:
    return use_update_state_with_latest_value(
        "id",
        "starting_after",
        state_key=current_starting_after_state_key(cfg.object_type),
        ascending=False,  # Stripe APIs are descending
    )


stripe_extract_records = use_extract_records_from_field("data")


def import_stripe_records(
    table: Table,
    state: State,
    cfg: StripeImporterConfig,
    write_records: ImporterContextFunction[None] = write_records_upsert,
) -> bool:
    update_state, update_request_with_state = stripe_use_update_state(cfg)
    finished = import_records(
        table,
        state,
        cfg,
        get_next_request=stripe_get_next_request,
        extract_records=stripe_extract_records,
        update_request_with_auth=stripe_update_request_with_auth,
        update_state=update_state,
        update_request_with_state=update_request_with_state,
        write_records=write_records,
    )
    if finished:
        state.set_value(latest_full_import_state_key(cfg.object_type), utcnow())
        # IMPORTANT: we reset the starting after cursor so we start from the beginning again on next run
        state.set_value(current_starting_after_state_key(cfg.object_type), None)
    return finished


def import_stripe_objects(
    table: Table,
    state: State,
    api_key: str,
    curing_window_days: int,
    object_type: str,
    request_params: dict = None,
    write_records: ImporterContextFunction[None] = write_records_upsert,
    secondary_store: Table = None,
    start_date: datetime = None,
) -> bool:
    cfg = StripeImporterConfig(
        api_key=api_key,
        curing_window_days=curing_window_days,
        object_type=object_type,
        request_params=request_params,
        secondary_store=secondary_store,
        start_date=start_date,
    )
    return import_stripe_records(table, state, cfg, write_records=write_records)


def _write_subscriptions_import_subscription_items(
    ctx: ImporterContext[StripeImporterConfig],
):
    if ctx.config.secondary_store.is_connected:
        for sub in ctx.latest_records:
            items_cfg = replace(
                ctx.config,
                object_type="subscription_items",
                request_params={"subscription": sub["id"]},
            )
            import_stripe_records(ctx.config.secondary_store, ctx.state, items_cfg)
    write_records_upsert(ctx)


def import_stripe_subscriptions(
    subscriptions_table: Table,
    items_table: Table,
    state: State,
    api_key: str,
    curing_window_days: int,
    start_date: datetime = None,
) -> bool:
    return import_stripe_objects(
        subscriptions_table,
        state,
        api_key,
        curing_window_days,
        object_type="subscriptions",
        request_params={"status": "all"},
        write_records=_write_subscriptions_import_subscription_items,
        secondary_store=items_table,
        start_date=start_date,
    )
