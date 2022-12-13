from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from patterns import State

from .base import (
    SquareImporterConfig,
    square_get_next_request,
    square_extract_records,
    square_update_request_with_auth,
    make_state_key,
)
from patterns_components.helpers.replication import import_records


def get_all_square_locations(state: State, access_token: str) -> list[dict]:
    locations = []
    write_locations = lambda ctx: locations.extend(ctx.latest_records)
    locations_cfg = SquareImporterConfig(
        access_token=access_token, object_type="locations"
    )
    import_records(
        None,  # Not used
        state,
        locations_cfg,
        get_next_request=square_get_next_request,
        extract_records=square_extract_records,
        update_request_with_auth=square_update_request_with_auth,
        write_records=write_locations,
    )
    return locations


def iterate_square_location_configs(
    state: State,
    cfg: SquareImporterConfig,
) -> Iterable[SquareImporterConfig]:
    locations = get_all_square_locations(state, cfg.access_token)
    for location in locations:
        state_key = make_state_key(location["id"])
        new_req_params = dict(**cfg.request_params, location_id=location["id"])
        new_cfg = replace(cfg, request_params=new_req_params, state_key=state_key)
        yield new_cfg
