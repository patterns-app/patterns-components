from __future__ import annotations

from typing import TYPE_CHECKING

from .importer_helpers import value_or_from_cfg

if TYPE_CHECKING:
    from .safe_enricher import EnricherContextFunction, EnricherContext, C


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
