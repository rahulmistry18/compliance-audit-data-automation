"""
Shared primitives used by every validator agent: a structured result object
and a tiny base class that gives each rule a consistent interface.

Keeping this framework-agnostic (no pandas types leaking into the dataclass)
makes RuleResult easy to serialize straight to CSV/JSON for the audit trail.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone


@dataclass
class RuleResult:
    rule_id: str
    domain: str            # e.g. "EMIR", "MiFID II", "Governance"
    entity_type: str        # e.g. "ledger_entry", "mandate"
    entity_id: str
    status: str              # "PASS" or "FAIL"
    severity: str            # LOW / MEDIUM / HIGH (meaningful only on FAIL)
    message: str
    evaluated_at: str = ""

    def __post_init__(self):
        if not self.evaluated_at:
            self.evaluated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self):
        return asdict(self)


class Rule:
    """
    Base class for a single compliance rule.

    Subclasses implement `evaluate(record) -> RuleResult`. Keeping one rule
    per class keeps each check independently testable and traceable back to
    a single rule_id in the audit trail.
    """

    rule_id: str = "BASE-000"
    domain: str = "Generic"
    entity_type: str = "record"

    def evaluate(self, record: dict) -> RuleResult:
        raise NotImplementedError

    def _pass(self, entity_id, message="OK", domain=None):
        return RuleResult(
            rule_id=self.rule_id,
            domain=domain or self.domain,
            entity_type=self.entity_type,
            entity_id=entity_id,
            status="PASS",
            severity="LOW",
            message=message,
        )

    def _fail(self, entity_id, severity, message, domain=None):
        return RuleResult(
            rule_id=self.rule_id,
            domain=domain or self.domain,
            entity_type=self.entity_type,
            entity_id=entity_id,
            status="FAIL",
            severity=severity,
            message=message,
        )
