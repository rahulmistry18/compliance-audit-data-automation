"""
LedgerValidatorAgent

A small "agent" in the sense that it autonomously runs its full battery of
rules over every ledger row and decides pass/fail/severity per rule per row,
without any per-row orchestration from the caller. It just needs a DataFrame
and returns a flat list of RuleResult objects ready for the audit trail.
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
    rule_id = "LEDGER-003"
    domain = "MiFID II"
    entity_type = "ledger_entry"

    def evaluate(self, row: dict) -> RuleResult:
        lei = row.get("counterparty_lei")
        if not isinstance(lei, str) or len(lei.strip()) != config.LEI_LENGTH:
            return self._fail(
                row["transaction_id"], config.SEVERITY_HIGH,
                f"counterparty_lei missing or not {config.LEI_LENGTH} characters."
            )
        return self._pass(row["transaction_id"])


class EMIRReportingDeadlineRule(Rule):
    rule_id = "EMIR-001"
    domain = "EMIR"
    entity_type = "ledger_entry"

    def evaluate(self, row: dict) -> RuleResult:
        trade_date = row.get("trade_date")
        reported_at = row.get("reporting_timestamp")

        if pd.isna(trade_date) or pd.isna(reported_at):
            return self._fail(
                row["transaction_id"], config.SEVERITY_HIGH,
                "Missing trade_date or reporting_timestamp for EMIR check."
            )

        deadline = trade_date + pd.Timedelta(days=config.EMIR_REPORTING_DEADLINE_DAYS)
        if reported_at > deadline:
            days_late = (reported_at - deadline).days
            return self._fail(
                row["transaction_id"], config.SEVERITY_HIGH,
                f"Reported {days_late} day(s) after the T+{config.EMIR_REPORTING_DEADLINE_DAYS} EMIR deadline."
            )
        return self._pass(row["transaction_id"])


class MiFIDFieldCompletenessRule(Rule):
    rule_id = "MIFID-001"
    domain = "MiFID II"
    entity_type = "ledger_entry"

    def evaluate(self, row: dict) -> RuleResult:
        missing = [
            f for f in config.MIFID_II_REQUIRED_FIELDS
            if row.get(f) is None or (isinstance(row.get(f), float) and np.isnan(row.get(f)))
            or (isinstance(row.get(f), str) and row.get(f).strip() == "")
            or pd.isna(row.get(f))
        ]
        if missing:
            return self._fail(
                row["transaction_id"], config.SEVERITY_HIGH,
                f"Missing required MiFID II field(s): {', '.join(missing)}."
            )
        return self._pass(row["transaction_id"])


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
            EMIRReportingDeadlineRule(),
            MiFIDFieldCompletenessRule(),
        ]

    def run(self) -> list:
        results = []
        for _, row in self.df.iterrows():
            record = row.to_dict()
            for rule in self.rules:
                results.append(rule.evaluate(record))
        return results
