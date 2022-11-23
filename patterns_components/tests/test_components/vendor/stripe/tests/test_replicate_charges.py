from datetime import timedelta

import requests_mock
from dcp.utils.common import utcnow

from patterns_components.tests.mock_api import MockOutputTable, MockState

from patterns_components.components.vendor.stripe.replication.base import (
    make_object_url,
    import_stripe_objects,
    current_starting_after_state_key,
    latest_full_import_state_key,
)


def test_replicate_charges():
    output_table = MockOutputTable()
    state = MockState()
    charges1 = [
        {"id": "ch1", "created": "2020-01-01"},
        {"id": "ch2", "created": "2020-01-02"},
    ]
    charges2 = [
        {"id": "ch3", "created": "2020-01-03"},
    ]
    charges_url = make_object_url("charges")
    with requests_mock.Mocker() as m:
        m.get(charges_url, json={"data": charges1})
        import_stripe_objects(
            table=output_table,
            state=state,
            api_key="Test",
            curing_window_days=90,
            object_type="charges",
        )
        assert m.last_request.url == "https://api.stripe.com/v1/charges?limit=100"
    assert len(output_table.get_test_records()) == 2
    assert state.state[current_starting_after_state_key("charges")] is None
    latest_import1 = state.state[latest_full_import_state_key("charges")]
    assert utcnow() - latest_import1 < timedelta(seconds=1)

    # Run again and make sure "full import" state is handled correctly
    output_table2 = MockOutputTable()
    with requests_mock.Mocker() as m:
        m.get(charges_url, json={"data": charges2})
        import_stripe_objects(
            table=output_table2,
            state=state,
            api_key="Test",
            curing_window_days=90,
            object_type="charges",
        )

        assert m.last_request.url.startswith(
            "https://api.stripe.com/v1/charges?limit=100&created%5Bgte%5D="
        )
    assert len(output_table2.get_test_records()) == 1
    assert state.state[current_starting_after_state_key("charges")] is None
    assert latest_import1 < state.state[latest_full_import_state_key("charges")]
