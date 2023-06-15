"""
Generates fully synthetic sample_ledger.csv and sample_mandates.csv files
so the workflow can be run and tested end-to-end without any real data.

A handful of records are deliberately seeded with issues (missing LEI, late
EMIR reporting, inconsistent mandate status, etc.) so the validator agents
have something to actually catch.
"""

import os
import numpy as np
import pandas as pd

np.random.seed(42)
os.makedirs("data", exist_ok=True)


def fake_lei(valid=True):
    if not valid:
        return "BADLEI123"  # too short -> fails LEI_LENGTH check
    return "".join(np.random.choice(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"), 20))


def build_ledger(n=25):
    rows = []
    base_date = pd.Timestamp("2023-05-01")

    for i in range(1, n + 1):
        trade_date = base_date + pd.Timedelta(days=int(np.random.randint(0, 25)))
        # Most entries report on time (T+1); a few are seeded late.
        late = i in (5, 14, 22)
        report_delay_days = np.random.choice([0, 1]) if not late else np.random.choice([2, 3, 4])
        reporting_timestamp = trade_date + pd.Timedelta(days=int(report_delay_days))

        is_debit = i % 2 == 0
        amount = round(float(np.random.uniform(1000, 500000)), 2)

        row = {
            "transaction_id": f"TXN-{1000 + i}",
            "trade_date": trade_date.date().isoformat(),
            "reporting_timestamp": reporting_timestamp.date().isoformat(),
            "counterparty_lei": fake_lei(valid=(i != 9)),  # TXN-1009 has a bad LEI
            "instrument_id": f"ISIN-DE000{np.random.randint(100000,999999)}" if i != 12 else "",
            "execution_timestamp": trade_date.isoformat(),
            "venue": np.random.choice(["XPAR", "XLON", "XFRA"]) if i != 17 else "",
            "price": round(float(np.random.uniform(90, 110)), 2) if i != 20 else np.nan,
            "debit": amount if is_debit else 0,
            "credit": 0 if is_debit else amount,
        }
        rows.append(row)

    # Seed one duplicate transaction_id
    dup = rows[3].copy()
    dup["transaction_id"] = rows[7]["transaction_id"]
    rows.append(dup)

    # Seed one entry with both debit and credit populated
    rows[10]["credit"] = 25000.00

    # Seed one entry with neither debit nor credit
    rows[15]["debit"] = 0
    rows[15]["credit"] = 0

    return pd.DataFrame(rows)


def build_mandates(n=12):
    rows = []
    base_start = pd.Timestamp("2020-01-01")

    for i in range(1, n + 1):
        start_date = base_start + pd.Timedelta(days=int(np.random.randint(0, 900)))
        mandate_id = f"MND-{200 + i}"

        if i in (2, 6, 9):  # active mandates, no termination in progress
            row = {
                "mandate_id": mandate_id,
                "client_name": f"Client {i}",
                "start_date": start_date.date().isoformat(),
                "termination_request_date": "",
                "termination_date": "",
                "status": "ACTIVE",
            }
        else:
            request_date = start_date + pd.Timedelta(days=int(np.random.randint(200, 800)))
            notice_days = int(np.random.choice([15, 30, 45, 60]))  # 15 seeds a short-notice fail
            termination_date = request_date + pd.Timedelta(days=notice_days)
            status = "TERMINATED"

            row = {
                "mandate_id": mandate_id,
                "client_name": f"Client {i}",
                "start_date": start_date.date().isoformat(),
                "termination_request_date": request_date.date().isoformat(),
                "termination_date": termination_date.date().isoformat(),
                "status": status,
            }
        rows.append(row)

    # Seed: termination_date before start_date
    rows[3]["termination_date"] = (base_start - pd.Timedelta(days=10)).date().isoformat()
    rows[3]["termination_request_date"] = (base_start - pd.Timedelta(days=40)).date().isoformat()

    # Seed: status ACTIVE but termination_date already passed
    rows[7]["status"] = "ACTIVE"
    rows[7]["termination_date"] = "2022-01-01"
    rows[7]["termination_request_date"] = "2021-11-01"

    # Seed: status TERMINATED but no termination_date recorded
    rows[10]["status"] = "TERMINATED"
    rows[10]["termination_date"] = ""

    # Seed: unrecognised status value
    rows[11]["status"] = "SUSPENDED"

    return pd.DataFrame(rows)


if __name__ == "__main__":
    ledger_df = build_ledger()
    mandates_df = build_mandates()

    ledger_df.to_csv("data/sample_ledger.csv", index=False)
    mandates_df.to_csv("data/sample_mandates.csv", index=False)

    print(f"Wrote {len(ledger_df)} rows to data/sample_ledger.csv")
    print(f"Wrote {len(mandates_df)} rows to data/sample_mandates.csv")
