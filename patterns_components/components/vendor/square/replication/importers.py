from __future__ import annotations

from patterns import Table, State
from requests import Request

from .base import (
    SquareImporterConfig,
    import_square_records_update_state,
    import_square_records,
    square_update_request_with_auth,
    square_extract_records,
    make_object_url,
)
from .locations import (
    iterate_square_location_configs,
)
from patterns_components.helpers.replication import (
    ImporterContext,
    import_records,
    ImporterContextFunction,
    write_records_default,
)


def import_square_payments(
    table: Table,
    state: State,
    access_token: str,
    write_records: ImporterContextFunction[None] = write_records_default,
):
    payments_cfg = SquareImporterConfig(
        access_token=access_token,
        object_type="payments",
        request_params={"sort_order": "ASC"},
    )
    for cfg in iterate_square_location_configs(state, payments_cfg):
        import_square_records_update_state(table, state, cfg, write_records)


def import_square_catalog_objects(table: Table, state: State, access_token: str):
    catalog_cfg = SquareImporterConfig(
        access_token=access_token,
        object_type="objects",
        request_params={"limit": 30},  # This is the max limit
    )
    import_square_records(table, state, catalog_cfg)


def import_square_customers(table: Table, state: State, access_token: str):
    customer_cfg = SquareImporterConfig(
        access_token=access_token,
        object_type="customers",
        request_params={
            "sort_order": "ASC",
            "sort_field": "CREATED_AT",
        },
    )
    import_square_records(table, state, customer_cfg)


def import_square_loyalty_accounts(table: Table, state: State, access_token: str):
    accounts_cfg = SquareImporterConfig(
        access_token=access_token,
        object_type="loyalty_accounts",
        request_params={
            "sort_order": "ASC",
            "sort_field": "CREATED_AT",
        },
    )
    import_square_records(table, state, accounts_cfg)


### Orders importer (nested special case)


def _write_payments_import_orders(ctx: ImporterContext[SquareImporterConfig]):
    _import_orders_from_payments(
        ctx.store, ctx.state, ctx.config.access_token, ctx.latest_records
    )


def _import_orders_from_payments(
    table: Table, state: State, access_token: str, payment_records: list[dict]
):
    orders_cfg = SquareImporterConfig(access_token=access_token, object_type="orders")
    batch_size = 100

    def get_next_request(
        prev_ctx: ImporterContext[SquareImporterConfig],
    ) -> Request | None:
        payment_batch = payment_records[
            (prev_ctx.iteration + 1)
            * batch_size : (prev_ctx.iteration + 2)
            * batch_size
        ]
        if not payment_batch:
            return None
        order_ids = [r["order_id"] for r in payment_batch if r.get("order_id")]
        return Request(
            "POST",
            make_object_url("orders/batch-retrieve"),
            json={"order_ids": order_ids},
        )

    import_records(
        table,
        state,
        orders_cfg,
        get_next_request=get_next_request,
        extract_records=square_extract_records,
        update_request_with_auth=square_update_request_with_auth,
    )


def import_square_orders(table: Table, state: State, access_token: str):
    import_square_payments(
        table, state, access_token, write_records=_write_payments_import_orders
    )
