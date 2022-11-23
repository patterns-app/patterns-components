import requests_mock

from patterns_components.tests.mock_api import MockOutputTable, MockState

from patterns_components.components.vendor.square.replication.base import (
    make_object_url,
    make_state_key,
    cursor_state_key,
)
from patterns_components.components.vendor.square.replication.importers import (
    import_square_orders,
    import_square_catalog_objects,
)


def test_replicate_orders():
    output_table = MockOutputTable()
    state = MockState()

    # Mock data
    locations = [{"id": "loc1"}, {"id": "loc2"}]
    payments = [
        {"order_id": "ord1", "created_at": "2020-01-01"},
        {"order_id": "ord2", "created_at": "2020-01-02"},
    ]
    orders = [{"id": "ord1"}, {"id": "ord2"}]
    access_token = "token"
    locations_url = make_object_url("locations")
    payments_url = make_object_url("payments")
    orders_url = make_object_url("orders/batch-retrieve")

    with requests_mock.Mocker() as m:
        # Mock requests
        m.get(locations_url, json={"locations": locations})
        m.get(payments_url, json={"payments": payments})
        m.post(orders_url, json={"orders": orders})
        import_square_orders(
            table=output_table,
            state=state,
            access_token=access_token,
        )
    assert (
        len(output_table.get_test_records()) == 2 * 2
    )  # 2 locations with 2 orders each
    assert state.state == {
        cursor_state_key: None,
        make_state_key("loc1"): "2020-01-02",
        make_state_key("loc2"): "2020-01-02",
    }


def test_catalog_objects_with_cursor():
    output_table = MockOutputTable()
    state = MockState()

    # Mock data
    objects = [
        {"id": "obj1", "created_at": "2020-01-01"},
        {"id": "obj2", "created_at": "2020-01-02"},
    ]
    objects2 = [
        {"id": "obj3", "created_at": "2020-01-03"},
    ]
    access_token = "token"
    objects_url = make_object_url("catalog/list")

    with requests_mock.Mocker() as m:
        # Mock requests
        m.get(objects_url, json={"objects": objects, "cursor": "cursor1"})
        m.get(objects_url + "?cursor=cursor1", json={"objects": objects2})
        import_square_catalog_objects(
            table=output_table,
            state=state,
            access_token=access_token,
        )
    assert len(output_table.get_test_records()) == 3
    assert state.state == {
        cursor_state_key: None,
    }
