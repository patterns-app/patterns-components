from datetime import timedelta

import requests_mock
from dcp.utils.common import utcnow

from patterns_components.tests.mock_api import MockOutputTable, MockState

from patterns_components.components.vendor.stripe.replication.base import (
    make_object_url,
    current_starting_after_state_key,
    latest_full_import_state_key,
    import_stripe_subscriptions,
)


def test_import_subscription_items():
    subs_table = MockOutputTable()
    items_table = MockOutputTable()
    state = MockState()
    subs = [
        {"id": "sub1", "created": "2020-01-01"},
        {"id": "sub2", "created": "2020-01-02"},
    ]
    items = [
        {"id": "it1", "created": "2020-01-01"},
        {"id": "it2", "created": "2020-01-02"},
        {"id": "it3", "created": "2020-01-03"},
    ]
    subscriptions_url = make_object_url("subscriptions")
    subscription_items_url = make_object_url("subscription_items")
    with requests_mock.Mocker() as m:
        m.get(subscriptions_url, json={"data": subs})
        m.get(subscription_items_url, json={"data": items})
        import_stripe_subscriptions(
            subs_table,
            items_table,
            state=state,
            api_key="Test",
            curing_window_days=90,
        )
        # Starts with since we ignore the created[gte] param
        assert m.last_request.url.startswith(
            "https://api.stripe.com/v1/subscription_items?limit=100&subscription=sub2"
        )
    assert len(subs_table.get_test_records()) == 2  # 2 subs
    assert len(items_table.get_test_records()) == 2 * 3  # 2 subs with 3 items each
    assert state.state[current_starting_after_state_key("subscriptions")] is None
    latest_import1 = state.state[latest_full_import_state_key("subscriptions")]
    assert utcnow() - latest_import1 < timedelta(seconds=1)
