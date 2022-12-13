from __future__ import annotations


from patterns import Table, Parameter, State, Connection

from patterns_components.helpers.replication import full_replication_manager
from .importers import (
    import_square_payments,
    import_square_orders,
    import_square_customers,
    import_square_catalog_objects,
    import_square_loyalty_accounts,
)

connection = Parameter(
    "connection", type=Connection("square"), description="Square Connection"
)
access_token = connection.get("api_key")

state = State()

square_payments = Table("square_payments", "w", schema="SquarePayment")
square_orders = Table("square_orders", "w", schema="SquareOrder")
square_customers = Table("square_customers", "w", schema="SquareCustomer")
square_catalog_objects = Table(
    "square_catalog_objects", "w", schema="SquareCatalogObject"
)
square_loyalty_accounts = Table(
    "square_loyalty_accounts", "w", schema="SquareLoyaltyAccount"
)


importers = [
    [
        "payments",
        lambda backfill: import_square_payments(square_payments, state, access_token),
    ],
    [
        "orders",
        lambda backfill: import_square_orders(square_orders, state, access_token),
    ],
    [
        "customers",
        lambda backfill: import_square_customers(
            square_loyalty_accounts, state, access_token
        ),
    ],
    [
        "catalog_objects",
        lambda backfill: import_square_catalog_objects(
            square_catalog_objects, state, access_token
        ),
    ],
    [
        "loyalty_accounts",
        lambda backfill: import_square_loyalty_accounts(
            square_loyalty_accounts, state, access_token
        ),
    ],
]

full_replication_manager(state, importers)
