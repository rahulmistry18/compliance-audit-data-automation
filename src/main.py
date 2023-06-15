"""
Orchestrator for the compliance audit data automation workflow.

Runs each validator "agent" independently over its slice of the data,
aggregates every rule evaluation into a single audit trail, and prints a
console summary with any HIGH-severity findings flagged for escalation.

Usage:
    python -m src.main
"""

import sys

from src import config
from src.data_loader import load_ledger, load_mandates, SchemaError
from src.validators.ledger_validator import LedgerValidatorAgent
from src.validators.mandate_validator import MandateValidatorAgent
from src.audit_trail import AuditTrail


def run_workflow(ledger_path=config.LEDGER_FILE, mandates_path=config.MANDATES_FILE):
    print("Compliance Audit Data Automation — PoC")
    print("=" * 60)

    try:
        ledger_df = load_ledger(ledger_path)
        mandates_df = load_mandates(mandates_path)
    except (SchemaError, FileNotFoundError) as exc:
        print(f"[FATAL] Could not load input data: {exc}")
        print("Tip: run `python generate_sample_data.py` to create sample CSVs first.")
        sys.exit(1)

    print(f"Loaded {len(ledger_df)} ledger entries and {len(mandates_df)} mandates.\n")

    print("Running LedgerValidatorAgent  (EMIR / MiFID II / bookkeeping rules)...")
    ledger_results = LedgerValidatorAgent(ledger_df).run()

    print("Running MandateValidatorAgent (termination governance rules)...")
    mandate_results = MandateValidatorAgent(mandates_df).run()

    all_results = ledger_results + mandate_results
    trail = AuditTrail(all_results)
    trail.write()
    trail.write_summary()

    total = len(all_results)
    failed = sum(1 for r in all_results if r.status == "FAIL")
    escalated = sum(
        1 for r in all_results
        if r.status == "FAIL" and r.severity == config.ESCALATION_THRESHOLD
    )

    print("\nResults")
    print("-" * 60)
    print(f"Total rule evaluations : {total}")
    print(f"Passed                 : {total - failed}")
    print(f"Failed                 : {failed}")
    print(f"Escalated (HIGH sev.)  : {escalated}")
    print(f"\nAudit trail written to : {config.AUDIT_TRAIL_CSV}")
    print(f"                          {config.AUDIT_TRAIL_JSON}")
    print(f"Summary written to     : {config.AUDIT_SUMMARY_CSV}")

    if escalated:
        print("\n[ESCALATION] The following findings require review:")
        for r in all_results:
            if r.status == "FAIL" and r.severity == config.ESCALATION_THRESHOLD:
                print(f"  - [{r.rule_id}] {r.entity_type} {r.entity_id}: {r.message}")

    return trail


if __name__ == "__main__":
    run_workflow()
