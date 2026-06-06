#!/usr/bin/env python3
"""Miroir Bloc 3 - Controle qualite (Great Expectations) sur le flux charge."""
import sys, pandas as pd
from sqlalchemy import create_engine
import great_expectations as gx
import great_expectations.expectations as gxe

URL = "postgresql+psycopg2://miroir:miroir_local_pwd@localhost:5432/miroir"
df = pd.read_sql(
    "SELECT t_dat, customer_id, article_id, price, sales_channel_id "
    "FROM signals.stream_transactions", create_engine(URL))
print(f"lignes lues: {len(df)}")

ctx = gx.get_context(mode="ephemeral")
ds = ctx.data_sources.add_pandas(name="miroir")
asset = ds.add_dataframe_asset(name="stream")
bdef = asset.add_batch_definition_whole_dataframe(name="whole")
suite = ctx.suites.add(gx.ExpectationSuite(name="miroir_stream"))
for e in [
    gxe.ExpectColumnValuesToNotBeNull(column="customer_id"),
    gxe.ExpectColumnValuesToNotBeNull(column="article_id"),
    gxe.ExpectColumnValuesToNotBeNull(column="t_dat"),
    gxe.ExpectColumnValuesToBeInSet(column="sales_channel_id", value_set=[1, 2]),
    gxe.ExpectColumnValuesToBeBetween(column="price", min_value=0, max_value=1),
    gxe.ExpectTableRowCountToBeBetween(min_value=1),
]:
    suite.add_expectation(e)

vd = ctx.validation_definitions.add(
    gx.ValidationDefinition(name="vd_stream", data=bdef, suite=suite))
res = vd.run(batch_parameters={"dataframe": df})

print("=== Great Expectations ===")
print("SUCCES GLOBAL:", res.success)
for r in res.results:
    c = r.expectation_config
    col = c.kwargs.get("column", "table")
    print(f"  [{'OK' if r.success else 'FAIL'}] {c.type} ({col})")
sys.exit(0 if res.success else 1)
