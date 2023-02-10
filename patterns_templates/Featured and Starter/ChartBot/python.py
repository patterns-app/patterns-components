from patterns import (
    Parameter,
    State,
    Table,
)
import sqlalchemy
from sqlalchemy.schema import CreateTable


print("hi")
eng = sqlalchemy.create_engine("postgresql://hmncerbyrjbqdjbitxngwadg%40psql-mock-database-cloud:ptrznvhuauqxboycbnsybukx@psql-mock-database-cloud.postgres.database.azure.com:5432/ecom1675318299004vjaefbbelylvraob")
metadata_obj = sqlalchemy.MetaData()

table = Table("schemas", "w")


def build_db_summary():
    summary = {}
    inspector = sqlalchemy.inspect(eng)
    for table in inspector.get_table_names():
        sa_table = sqlalchemy.Table(table, metadata_obj, autoload_with=eng)
        s = CreateTable(sa_table).compile(eng)
        summary[table] = str(s)
    return summary


s = build_db_summary()
table.replace({"schemas": s})