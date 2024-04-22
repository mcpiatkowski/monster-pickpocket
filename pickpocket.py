"""Scrapped data transformation."""

import argparse

import numpy as np
import pandas as pd


def main(record_date: str) -> None:
    """Execute main function."""
    ram = pd.read_parquet(f"data/{record_date}/ram.parquet")

    ram["multiplier"] = ram["inactive"].str.extract(r"(\d+)").astype(int)

    conditions = [
        ram["inactive"].str.contains("days?", regex=True),
        ram["inactive"].str.contains("months?", regex=True),
        ram["inactive"].str.contains("years?", regex=True),
    ]

    values = [
        (ram["multiplier"] * pd.Timedelta(days=1)).astype(str),
        (ram["multiplier"] * pd.Timedelta(days=30)).astype(str),
        (ram["multiplier"] * pd.Timedelta(days=365)).astype(str),
    ]

    ram["inactive_days"] = pd.to_timedelta(np.select(conditions, values))

    print(
        ram[ram.inactive_days >= pd.Timedelta(days=10)]
        .drop(columns="multiplier", axis=1)
        .sort_values(by="earnings", ascending=False)
        .reset_index(drop=True)
        .head(10)
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transform ram data.")
    parser.add_argument("-d", "--record-date", dest="record_date", type=str, required=True)
    args = parser.parse_args()

    main(args.record_date)
