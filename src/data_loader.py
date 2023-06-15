"""
Loads the raw ledger and mandate CSVs into pandas DataFrames and performs
lightweight schema validation before any compliance rule ever sees the data.
Failing fast here keeps downstream validator agents simple.
"""

import pandas as pd

LEDGER_SCHEMA = [
    "transaction_id",
    "trade_date",
    "reporting_timestamp",
    "counterparty_lei",
    "instrument_id",
    "execution_timestamp",
    "venue",
    "price",
    "debit",
    "credit",
]

MANDATE_SCHEMA = [
    "mandate_id",
    "client_name",
    "start_date",
    "termination_request_date",
    "termination_date",
    "status",
]


class SchemaError(Exception):
    pass


def _validate_columns(df: pd.DataFrame, expected: list, name: str):
    missing = set(expected) - set(df.columns)
    if missing:
        raise SchemaError(f"{name} is missing required columns: {sorted(missing)}")


def load_ledger(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    _validate_columns(df, LEDGER_SCHEMA, "Ledger")

    date_cols = ["trade_date", "reporting_timestamp", "execution_timestamp"]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    return df


def load_mandates(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    _validate_columns(df, MANDATE_SCHEMA, "Mandates")

    date_cols = ["start_date", "termination_request_date", "termination_date"]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    return df
