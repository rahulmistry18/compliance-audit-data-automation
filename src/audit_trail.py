"""
Audit trail: takes the flat list of RuleResult objects produced by every
validator agent and persists them so any finding can be traced back to the
exact rule, entity, timestamp, and message that produced it.
"""

import json
import os

import pandas as pd

from src import config


class AuditTrail:
    def __init__(self, results: list):
        self.results = results
        self.df = pd.DataFrame([r.to_dict() for r in results])

    def write(self, csv_path=config.AUDIT_TRAIL_CSV, json_path=config.AUDIT_TRAIL_JSON):
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        self.df.to_csv(csv_path, index=False)
        with open(json_path, "w") as f:
            json.dump([r.to_dict() for r in self.results], f, indent=2, default=str)

    def summary(self) -> pd.DataFrame:
        if self.df.empty:
            return pd.DataFrame(
                columns=["rule_id", "domain", "total", "passed", "failed", "escalated"]
            )

        grouped = self.df.groupby(["rule_id", "domain"])
        summary_rows = []
        for (rule_id, domain), group in grouped:
            failed = group[group["status"] == "FAIL"]
            escalated = failed[failed["severity"] == config.ESCALATION_THRESHOLD]
            summary_rows.append(
                {
                    "rule_id": rule_id,
                    "domain": domain,
                    "total": len(group),
                    "passed": len(group[group["status"] == "PASS"]),
                    "failed": len(failed),
                    "escalated": len(escalated),
                }
            )
        return pd.DataFrame(summary_rows).sort_values(["escalated", "failed"], ascending=False)

    def write_summary(self, csv_path=config.AUDIT_SUMMARY_CSV):
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        self.summary().to_csv(csv_path, index=False)
