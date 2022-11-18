from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from commonmodel import Schema
from dcp import Storage
from dcp.utils.common import ensure_datetime, utcnow


@dataclass
class MockTableVersion:
    name: str
    storage: Storage
    schema: Schema | None = None
    _records: list[dict] = None

    def set_schema(self, schema: Schema):
        self.schema = schema

    @property
    def exists(self) -> bool:
        return bool(self._records)

    @property
    def record_count(self) -> int | None:
        return len(self._records) if self._records else None


class MockIoBase:
    def __init__(self, records: list[dict] = None, name: str = "_test", **kwargs):
        self._records = records
        self._name = name
        self.table = MockTableVersion(
            name=self._name, storage=Storage("python://_test"), _records=self._records
        )
        self.schemas: dict[str, Schema] = {}
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def is_connected(self):
        return True

    def get_test_records(self) -> list[dict]:
        return self._records

    def has_active_version(self) -> bool:
        return self._records is not None

    def get_active_version(self) -> MockTableVersion | None:
        return self.table

    def set_active_version(self, table: MockTableVersion):
        self.table = table

    def create_new_version(self) -> MockTableVersion:
        return self.table or MockTableVersion(
            name=self._name, storage=Storage("python://_output_test")
        )

    @property
    def sql_name(self) -> str:
        if not self.exists:
            return None
        return self.table.name

    @property
    def storage(self) -> Storage:
        return self.table.storage

    @property
    def exists(self) -> bool:
        return self.table.exists

    @property
    def record_count(self) -> int | None:
        return self.table.record_count

    def _write(self, records, replace=False):
        if replace or not self._records:
            self._records = records
            if self.table is None:
                self.set_active_version(self.create_new_version())
            self.table._records = records
        else:
            self._records.extend(records)


class MockInputTable(MockIoBase):
    def __init__(self, records: list[dict] = None, **kwargs):
        super().__init__(records, **kwargs)
        self._streams = {}

    def read(self, as_format, chunksize=None):
        if as_format == "dataframe":
            return self.read_dataframe()
        return self.get_test_records()

    def read_dataframe(self, chunksize: int = None):
        if chunksize:
            raise NotImplementedError
        import pandas

        return pandas.DataFrame.from_records(self._records)

    def read_sql(self, sql: str, chunksize: int = None) -> Iterator[list[dict]]:
        with self.dbapi.execute_sql_result(sql) as res:
            records = [r._mapping for r in res]
        if chunksize:
            # just one chunk
            yield records
        else:
            return records

    def as_stream(self, order_by: str = None, starting_value=None):
        if order_by not in self._streams:
            self._streams[order_by] = MockTableStream(self.get_test_records())
        return self._streams[order_by]


class MockTableStream(MockIoBase):
    def __init__(self, records: list[dict] = None, **kwargs):
        super().__init__(records, **kwargs)
        self._write(records, replace=True)
        self._record_index = 0

    def consume_records(self, with_metadata=False) -> Iterator[dict]:
        if not self.has_active_version() or not self._records:
            return

        while True:
            if self._record_index >= len(self._records):
                return
            r = self._records[self._record_index]
            self._record_index += 1
            if with_metadata:
                yield r
                # yield {"timestamp": utcnow(), "record": r}
            else:
                yield r["record"]

    def __iter__(self) -> Iterator[dict]:
        yield from self.consume_records()

    def rollback(self):
        pass

    def rewind(self):
        self._record_index = 0


class MockOutputTable(MockIoBase):
    def init(self, name: str = "_output_test", **kwargs):
        super().__init__(None, name=name, **kwargs)

    def _write_any(self, records, replace=False):
        if isinstance(records, list):
            self._write_records(records, replace)
        else:
            self._write_dataframe(records, replace)

    def upsert(self, records):
        self._write_any(records)

    def append(self, records):
        self._write_any(records)

    def replace(self, records):
        self._write_any(records, replace=True)

    def _write_records(self, records, replace=False):
        self._write(records, replace)

    def _write_dataframe(self, dataframe, replace=False):
        records = dataframe.to_dict("records")
        self._write_records(records, replace=replace)

    def execute_sql(self, sql, **kwargs):
        # TODO: Must manually add dbapi attr if you want this...
        self.dbapi.execute_sql(sql)

    def signal_create(self, *args, **kwargs):
        if not self._records:
            # Not-null
            self._write([{}], replace=True)

    def signal_update(self, *args, **kwargs):
        if not self._records:
            raise Exception("Can't update when not existing")


class MockState:
    def __init__(self, **kwargs):
        self.state = {}
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_value(self, k, default=None):
        return self.state.get(k, default)

    def set_value(self, k, v):
        self.state[k] = v

    def should_continue(self):
        return True

    def request_new_run(self, *args, **kwargs):
        pass

    def get_datetime(self, k, d=None):
        return ensure_datetime(self.get_value(k, d))
