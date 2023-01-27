from patterns import (
    Parameter,
    State,
    Table,
)

in_table = Table("webhook")
out_table = Table("table", "w")

# Add an auto timestamp to the table, this will give the table a default
# ordering so it can easily be streamed
out_table.init(add_created="timestamp")

for record in in_table.as_stream().consume_records():
    # Do something with the record
    # out_table.append(record)
    ...
