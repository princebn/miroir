# Quality gate Great Expectations sur train.parquet (avant retrain).
# Exit 0 si SUCCES, 1 si echec -> stoppe le DAG.
from __future__ import annotations

import sys
from pathlib import Path

import great_expectations as gx
import great_expectations.expectations as gxe
import pandas as pd

TRAIN_PATH = Path(__file__).resolve().parent.parent / "data" / "synthetic" / "train.parquet"


def main():
    df = pd.read_parquet(TRAIN_PATH)
    print(f"train.parquet : {len(df)} lignes, {len(df.columns)} colonnes")
    ctx = gx.get_context(mode="ephemeral")
    ds = ctx.data_sources.add_pandas("local")
    asset = ds.add_dataframe_asset("train")
    bdef = asset.add_batch_definition_whole_dataframe("whole")
    suite = ctx.suites.add(gx.ExpectationSuite("retrain_quality"))
    for e in [
        gxe.ExpectColumnValuesToNotBeNull(column="__label"),
        gxe.ExpectColumnValuesToBeInSet(column="__label", value_set=[0, 1]),
        gxe.ExpectColumnValuesToNotBeNull(column="__client_id"),
        gxe.ExpectTableRowCountToBeBetween(min_value=20000),
        gxe.ExpectColumnMeanToBeBetween(column="__label", min_value=0.10, max_value=0.25),
    ]:
        suite.add_expectation(e)
    vd = ctx.validation_definitions.add(
        gx.ValidationDefinition(name="vd_retrain", data=bdef, suite=suite)
    )
    res = vd.run(batch_parameters={"dataframe": df})
    print("=== Great Expectations ===")
    print("SUCCES GLOBAL:", res.success)
    for r in res.results:
        c = r.expectation_config
        col = c.kwargs.get("column", "table")
        flag = "OK" if r.success else "FAIL"
        print(f"  [{flag}] {c.type} ({col})")
    sys.exit(0 if res.success else 1)


if __name__ == "__main__":
    main()
