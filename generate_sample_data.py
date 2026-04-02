"""
Generates fully synthetic sample_ledger.csv and sample_mandates.csv files
so the workflow can be run and tested end-to-end without any real data.

Names, instruments, and identifiers here are fabricated to look realistic
(plausible fund names, instrument types, currencies) but are entirely
fictional - they do not reference any real company, trade, or contract.

Ledger entries are spread across three jurisdictions (EU / US / APAC) so the
ReportingDeadlineRule and CDECompletenessRule can demonstrate genuinely
different regulatory deadlines (EU T+1, US same-day, APAC T+2). A handful of
records are deliberately seeded with issues (late reporting, missing LEI,
missing CDE fields, inconsistent mandate status, etc.) so the validator
agents have something to actually catch.
"""

import os
import numpy as np
import pandas as pd

np.random.seed(42)
os.makedirs("data", exist_ok=True)

JURISDICTIONS = ["EU", "US", "APAC"]
DEADLINE_DAYS = {"EU": 1, "US": 0, "APAC": 2}

VENUES = {"EU": ["XPAR", "XLON", "XFRA"], "US": ["XNYS", "XNAS"], "APAC": ["XASX", "XHKG", "XSES"]}
CURRENCIES = {"EU": "EUR", "US": "USD", "APAC": "AUD"}

INSTRUMENTS = [
    ("Interest Rate Swap 5Y", "IRS"),
    ("Interest Rate Swap 10Y", "IRS"),
    ("FX Forward EUR/USD", "FXF"),
    ("FX Forward USD/JPY", "FXF"),
    ("Credit Default Swap", "CDS"),
    ("Equity Index Option", "EQO"),
    ("Cross-Currency Swap", "XCS"),
    ("Commodity Swap - Brent", "CMS"),
]

COUNTERPARTY_NAMES = [
    "Alderbrook Capital LLP", "Solano Ridge Asset Management", "Kestrel Harbor Investments",
    "Northbridge Capital Partners", "Farview Global Markets", "Cedarline Asset Advisors",
    "Windmere Trading LLC", "Blackthorn Capital Group", "Silverpine Financial Ltd",
    "Harborstone Investment Partners", "Meridian Ridge Capital", "Oakfield Global Advisors",
]


def fake_lei(valid=True):
    if not valid:
        return "BADLEI123"  # too short -> fails LEI_LENGTH check
    return "".join(np.random.choice(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"), 20))


def build_ledger(n=30):
    rows = []
    base_date = pd.Timestamp("2023-05-01")
    jurisdictions = [JURISDICTIONS[i % 3] for i in range(n)]
    late_indices = {5, 14, 22, 27}

    for i in range(1, n + 1):
        jurisdiction = jurisdictions[i - 1]
        deadline_days = DEADLINE_DAYS[jurisdiction]

        trade_date = base_date + pd.Timedelta(days=int(np.random.randint(0, 25)))
        late = i in late_indices
        if late:
            report_delay_days = deadline_days + int(np.random.choice([1, 2, 3]))
        else:
            report_delay_days = int(np.random.choice(range(0, deadline_days + 1))) if deadline_days > 0 else 0
        reporting_timestamp = trade_date + pd.Timedelta(days=report_delay_days)

        is_debit = i % 2 == 0
        amount = round(float(np.random.uniform(50_000, 4_800_000)) / 100, 2) * 100
        instrument_name, instrument_prefix = INSTRUMENTS[i % len(INSTRUMENTS)]
        counterparty_name = COUNTERPARTY_NAMES[i % len(COUNTERPARTY_NAMES)]

        row = {
            "transaction_id": f"TXN-{1000 + i}",
            "jurisdiction": jurisdiction,
            "currency": CURRENCIES[jurisdiction],
            "counterparty_name": counterparty_name,
            "trade_date": trade_date.date().isoformat(),
            "reporting_timestamp": reporting_timestamp.date().isoformat(),
            "counterparty_lei": fake_lei(valid=(i != 9)),  # TXN-1009 has a bad LEI
            "instrument_id": f"{instrument_prefix}-{2023}{np.random.randint(1000,9999)}" if i != 12 else "",
            "instrument_name": instrument_name,
            "execution_timestamp": trade_date.isoformat(),
            "venue": np.random.choice(VENUES[jurisdiction]) if i != 17 else "",
            "price": round(float(np.random.uniform(90, 110)), 2) if i != 20 else np.nan,
            "debit": amount if is_debit else 0,
            "credit": 0 if is_debit else amount,
        }
        rows.append(row)

    dup = rows[3].copy()
    dup["transaction_id"] = rows[7]["transaction_id"]
    rows.append(dup)

    rows[10]["credit"] = 25000.00
    rows[15]["debit"] = 0
    rows[15]["credit"] = 0

    return pd.DataFrame(rows)


def build_mandates(n=12):
    rows = []
    base_start = pd.Timestamp("2020-01-01")

    for i in range(1, n + 1):
        start_date = base_start + pd.Timedelta(days=int(np.random.randint(0, 900)))
        mandate_id = f"MND-{200 + i}"
        client_name = COUNTERPARTY_NAMES[(i + 5) % len(COUNTERPARTY_NAMES)]

        if i in (2, 6, 9):
            row = {
                "mandate_id": mandate_id,
                "client_name": client_name,
                "start_date": start_date.date().isoformat(),
                "termination_request_date": "",
                "termination_date": "",
                "status": "ACTIVE",
            }
        else:
            request_date = start_date + pd.Timedelta(days=int(np.random.randint(200, 800)))
            notice_days = int(np.random.choice([15, 30, 45, 60]))
            termination_date = request_date + pd.Timedelta(days=notice_days)
            status = "TERMINATED"

            row = {
                "mandate_id": mandate_id,
                "client_name": client_name,
                "start_date": start_date.date().isoformat(),
                "termination_request_date": request_date.date().isoformat(),
                "termination_date": termination_date.date().isoformat(),
                "status": status,
            }
        rows.append(row)

    rows[3]["termination_date"] = (base_start - pd.Timedelta(days=10)).date().isoformat()
    rows[3]["termination_request_date"] = (base_start - pd.Timedelta(days=40)).date().isoformat()

    rows[7]["status"] = "ACTIVE"
    rows[7]["termination_date"] = "2022-01-01"
    rows[7]["termination_request_date"] = "2021-11-01"

    rows[10]["status"] = "TERMINATED"
    rows[10]["termination_date"] = ""

    rows[11]["status"] = "SUSPENDED"

    return pd.DataFrame(rows)


if __name__ == "__main__":
    ledger_df = build_ledger()
    mandates_df = build_mandates()

    ledger_df.to_csv("data/sample_ledger.csv", index=False)
    mandates_df.to_csv("data/sample_mandates.csv", index=False)

    print(f"Wrote {len(ledger_df)} rows to data/sample_ledger.csv")
    print(f"Wrote {len(mandates_df)} rows to data/sample_mandates.csv")
