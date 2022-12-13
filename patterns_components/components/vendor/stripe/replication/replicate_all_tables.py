from __future__ import annotations

from datetime import datetime

from patterns import Table, Parameter, State, Connection

from patterns_components.helpers.replication import full_replication_manager
from .base import (
    import_stripe_objects,
    import_stripe_subscriptions,
)

_api_key_desc = "Obtain from https://dashboard.stripe.com/apikeys. Must be a *secret* key, not a *publishable* key."
connection = Parameter(
    "connection", type=Connection("stripe"), description="Stripe connection"
)
api_key = Parameter("api_key", type=str, description=_api_key_desc, default=None)
curing_window_days = Parameter(
    "curing_window_days",
    type=int,
    default=90,
    description="How many days back to look for updated records",
)
start_date = Parameter(
    "start_date",
    type=datetime,
    default=None,
    description="Date from which to start pulling fact tables. (Dimension tables pulled from all-time regardless)",
)

state = State()

stripe_charges = Table("stripe_charges", "w", schema="StripeCharge")
stripe_invoices = Table("stripe_invoices", "w", schema="StripeInvoice")
stripe_refunds = Table("stripe_refunds", "w", schema="StripeRefund")
stripe_subscriptions = Table("stripe_subscriptions", "w", schema="StripeSubscription")
stripe_subscription_items = Table(
    "stripe_subscription_items", "w", schema="StripeSubscriptionItem"
)


standard_tables = [
    ["charges", stripe_charges],
    ["invoices", stripe_invoices],
    ["refunds", stripe_refunds],
]


api_key = api_key or connection.get("api_key")
if not api_key:
    raise Exception("Must provide a Stripe Connection or an explicit api_key")

importers = []


def make_importer(obj_type: str, table: Table):
    return lambda backfill: import_stripe_objects(
        table,
        state,
        api_key,
        1 if backfill else curing_window_days,
        obj_type,
        start_date=start_date,
    )


for obj_type, table in standard_tables:
    if not table.is_connected:
        continue
    importers.append(
        [
            obj_type,
            make_importer(obj_type, table),
        ]
    )

if stripe_subscriptions.is_connected:
    importers.append(
        (
            "subscriptions",
            lambda backfill: import_stripe_subscriptions(
                stripe_subscriptions,
                stripe_subscription_items,
                state,
                api_key,
                1 if backfill else curing_window_days,
                start_date=start_date,
            ),
        )
    )

full_replication_manager(state, importers)
