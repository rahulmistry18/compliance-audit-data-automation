"""
MandateValidatorAgent

Governance checks on the mandate lifecycle, focused on the audit finding
that shows up most often in practice: termination dates and status flags
that quietly drift out of sync with each other.
"""

import pandas as pd

from src import config
from src.validators.compliance_rules import Rule, RuleResult

VALID_STATUSES = {"ACTIVE", "TERMINATED", "PENDING_TERMINATION"}


class TerminationAfterStartRule(Rule):
    rule_id = "MANDATE-001"
    domain = "Governance"
    entity_type = "mandate"

    def evaluate(self, row: dict) -> RuleResult:
        start = row.get("start_date")
        term = row.get("termination_date")
        if pd.isna(term):
            return self._pass(row["mandate_id"], "No termination date set; not applicable.")
        if pd.isna(start):
            return self._fail(
                row["mandate_id"], config.SEVERITY_HIGH, "Missing start_date."
            )
        if term < start:
            return self._fail(
                row["mandate_id"], config.SEVERITY_HIGH,
                "termination_date is earlier than start_date."
            )
        return self._pass(row["mandate_id"])


class MinimumNoticePeriodRule(Rule):
    rule_id = "MANDATE-002"
    domain = "Governance"
    entity_type = "mandate"

    def evaluate(self, row: dict) -> RuleResult:
        request_date = row.get("termination_request_date")
        term = row.get("termination_date")
        if pd.isna(request_date) or pd.isna(term):
            return self._pass(row["mandate_id"], "Not applicable; no termination in progress.")

        notice_days = (term - request_date).days
        if notice_days < config.MANDATE_MIN_NOTICE_DAYS:
            return self._fail(
                row["mandate_id"], config.SEVERITY_MEDIUM,
                f"Only {notice_days} day(s) notice given; minimum required is "
                f"{config.MANDATE_MIN_NOTICE_DAYS} day(s)."
            )
        return self._pass(row["mandate_id"])


class StatusConsistencyRule(Rule):
    rule_id = "MANDATE-003"
    domain = "Governance"
    entity_type = "mandate"

    def evaluate(self, row: dict) -> RuleResult:
        status = str(row.get("status", "")).strip().upper()
        term = row.get("termination_date")
        today = pd.Timestamp.now(tz=None).normalize()

        if status not in VALID_STATUSES:
            return self._fail(
                row["mandate_id"], config.SEVERITY_MEDIUM,
                f"Unrecognised status value: '{row.get('status')}'."
            )

        if status == "ACTIVE" and pd.notna(term) and term <= today:
            return self._fail(
                row["mandate_id"], config.SEVERITY_HIGH,
                "Status is ACTIVE but termination_date has already passed."
            )

        if status == "TERMINATED" and pd.isna(term):
            return self._fail(
                row["mandate_id"], config.SEVERITY_HIGH,
                "Status is TERMINATED but no termination_date is recorded."
            )

        return self._pass(row["mandate_id"])


class MandateValidatorAgent:
    """Runs the full mandate rule set and returns a flat list of RuleResults."""

    def __init__(self, mandates_df: pd.DataFrame):
        self.df = mandates_df
        self.rules = [
            TerminationAfterStartRule(),
            MinimumNoticePeriodRule(),
            StatusConsistencyRule(),
        ]

    def run(self) -> list:
        results = []
        for _, row in self.df.iterrows():
            record = row.to_dict()
            for rule in self.rules:
                results.append(rule.evaluate(record))
        return results
