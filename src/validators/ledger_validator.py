"""
LedgerValidatorAgent

Each rule below runs autonomously over every ledger row and returns a
RuleResult, without any per-row orchestration from the caller - that's the
"agentic" part: hand it a DataFrame, get back a fully traced set of findings.

Two rules are jurisdiction-aware (ReportingDeadlineRule, CDECompletenessRule)
because trade reporting is genuinely different by region:

  EU    - EMIR REFIT / MiFID II RTS 22, reported to ESMA-regulated trade
           repositories, deadline T+1.
  US    - Dodd-Frank Title VII, split between the CFTC (swaps) and SEC
           (security-based swaps under Reg SBSR), reporting required "as
           soon as technologically practicable" - modelled here as same-day.
  APAC  - Australia's ASIC 2024 Rules, Hong Kong's SFC/HKMA regime, and
           Singapore's MAS rules, which all moved to a harmonised T+2 in
           their 2024–2025 rewrites.

See config.py and the README's "Global regulatory landscape" section for
the reasoning and sources behind these numbers.
"""

import numpy as np
import pandas as pd

from src import config
from src.validators.compliance_rules import Rule, RuleResult


class DebitCreditBalanceRule(Rule):
    rule_id = "LEDGER-001"
    domain = "Bookkeeping"
    entity_type = "ledger_entry"

    def evaluate(self, row: dict) -> RuleResult:
        debit = row.get("debit", 0) or 0
        credit = row.get("credit", 0) or 0
        if debit == 0 and credit == 0:
            return self._fail(
                row["transaction_id"], config.SEVERITY_MEDIUM,
                "Entry has neither a debit nor a credit amount."
            )
        if debit != 0 and credit != 0:
            return self._fail(
                row["transaction_id"], config.SEVERITY_HIGH,
                "Entry has both a debit and a credit amount populated."
            )
        return self._pass(row["transaction_id"])


class DuplicateTransactionRule(Rule):
    rule_id = "LEDGER-002"
    domain = "Bookkeeping"
    entity_type = "ledger_entry"

    def __init__(self, duplicate_ids: set):
        self.duplicate_ids = duplicate_ids

    def evaluate(self, row: dict) -> RuleResult:
        if row["transaction_id"] in self.duplicate_ids:
            return self._fail(
                row["transaction_id"], config.SEVERITY_HIGH,
                "Duplicate transaction_id detected in ledger."
            )
        return self._pass(row["transaction_id"])


class CounterpartyLEIRule(Rule):
    """
    LEI (ISO 17442) is the one identifier every jurisdiction modelled here
    already agrees on, so this rule doesn't need to branch by jurisdiction.
    """
    rule_id = "LEDGER-003"
    domain = "Counterparty Identification (Global - ISO 17442)"
    entity_type = "ledger_entry"

    def evaluate(self, row: dict) -> RuleResult:
        lei = row.get("counterparty_lei")
        if not isinstance(lei, str) or len(lei.strip()) != config.LEI_LENGTH:
            return self._fail(
                row["transaction_id"], config.SEVERITY_HIGH,
                f"counterparty_lei missing or not {config.LEI_LENGTH} characters."
            )
        return self._pass(row["transaction_id"])


class ReportingDeadlineRule(Rule):
    """
    Generalised trade-reporting deadline check. The deadline and the
    regulatory label applied both depend on the row's `jurisdiction` field -
    this is what makes the rule genuinely cross-border rather than EU-only.
    """
    rule_id = "REPORT-001"
    domain = "Trade Reporting Deadline"
    entity_type = "ledger_entry"

    def evaluate(self, row: dict) -> RuleResult:
        jurisdiction = row.get("jurisdiction")
        trade_date = row.get("trade_date")
        reported_at = row.get("reporting_timestamp")
        label = config.JURISDICTION_LABELS.get(jurisdiction, jurisdiction)

        if jurisdiction not in config.REPORTING_DEADLINE_DAYS:
            return self._fail(
                row["transaction_id"], config.SEVERITY_MEDIUM,
                f"Unrecognised jurisdiction '{jurisdiction}'; cannot determine reporting deadline.",
                domain=label,
            )

        if pd.isna(trade_date) or pd.isna(reported_at):
            return self._fail(
                row["transaction_id"], config.SEVERITY_HIGH,
                "Missing trade_date or reporting_timestamp for reporting-deadline check.",
                domain=label,
            )

        deadline_days = config.REPORTING_DEADLINE_DAYS[jurisdiction]
        deadline = trade_date + pd.Timedelta(days=deadline_days)
        if reported_at > deadline:
            days_late = (reported_at - deadline).days
            return self._fail(
                row["transaction_id"], config.SEVERITY_HIGH,
                f"Reported {days_late} day(s) after the {jurisdiction} T+{deadline_days} deadline ({label}).",
                domain=label,
            )
        return self._pass(row["transaction_id"], domain=label)


class CDECompletenessRule(Rule):
    """
    Checks the shared "Critical Data Elements" (CPMI-IOSCO) field set that
    MiFID II RTS 22 (EU), CFTC Parts 43/45 (US), and the ASIC/HKMA-SFC/MAS
    rewrites (APAC) have converged on. The required fields are the same
    everywhere in this simplified PoC; the domain label still reflects the
    row's jurisdiction so findings are traceable to the right regime.
    """
    rule_id = "CDE-001"
    domain = "Critical Data Elements (CDE)"
    entity_type = "ledger_entry"

    def evaluate(self, row: dict) -> RuleResult:
        jurisdiction = row.get("jurisdiction")
        label = config.JURISDICTION_LABELS.get(jurisdiction, jurisdiction)

        missing = [
            f for f in config.CDE_REQUIRED_FIELDS
            if row.get(f) is None or (isinstance(row.get(f), float) and np.isnan(row.get(f)))
            or (isinstance(row.get(f), str) and row.get(f).strip() == "")
            or pd.isna(row.get(f))
        ]
        if missing:
            return self._fail(
                row["transaction_id"], config.SEVERITY_HIGH,
                f"Missing required Critical Data Element(s): {', '.join(missing)}.",
                domain=label,
            )
        return self._pass(row["transaction_id"], domain=label)


class LedgerValidatorAgent:
    """Runs the full ledger rule set and returns a flat list of RuleResults."""

    def __init__(self, ledger_df: pd.DataFrame):
        self.df = ledger_df
        duplicate_ids = set(
            ledger_df.loc[ledger_df["transaction_id"].duplicated(keep=False), "transaction_id"]
        )
        self.rules = [
            DebitCreditBalanceRule(),
            DuplicateTransactionRule(duplicate_ids),
            CounterpartyLEIRule(),
            ReportingDeadlineRule(),
            CDECompletenessRule(),
        ]

    def run(self) -> list:
        results = []
        for _, row in self.df.iterrows():
            record = row.to_dict()
            for rule in self.rules:
                results.append(rule.evaluate(record))
        return results
