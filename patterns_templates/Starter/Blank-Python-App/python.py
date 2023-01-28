from patterns import (
    Parameter,
    State,
    Table,
)

table = Table("table", "w")


"""
Writing to Tables:

# Write list of dictionaries or pandas DataFrame
records = [{"a": i} for i in range(10)]
table.append(records)
df = pd.DataFrame.from_records(records)
table.append(df)

# Replace the table wholesale with new records (creates a new table version)
table.replace(df)

# Alternatively, can declare a unique index and upsert
table.init(unique_on="a")
table.upsert(records)
table.upsert(records)  # All duplicates, no effect
"""
