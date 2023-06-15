"""
Central configuration for the compliance audit workflow.

Keeping thresholds and deadlines here (rather than hard-coded inside rules)
means the rule set can be re-tuned per jurisdiction/desk without touching
validator logic.
"""

# --- EMIR ---------------------------------------------------------------
# Trades must generally be reported to a trade repository by T+1.
EMIR_REPORTING_DEADLINE_DAYS = 1

# --- MiFID II (RTS 22 transaction reporting) -----------------------------
# Fields that must be populated for a ledger entry to be MiFID II compliant.
MIFID_II_REQUIRED_FIELDS = [
    "instrument_id",
    "execution_timestamp",
    "venue",
    "price",
    "counterparty_lei",
]

# A Legal Entity Identifier is a 20-character alphanumeric code (ISO 17442).
LEI_LENGTH = 20

# --- Mandate governance ---------------------------------------------------
# Minimum contractual notice period (in days) required before a mandate's
# termination date, measured from the request/decision date.
MANDATE_MIN_NOTICE_DAYS = 30

# --- Ledger integrity ------------------------------------------------------
# Tolerance for floating point comparisons on monetary amounts.
AMOUNT_TOLERANCE = 0.01

# --- Severity levels used across all validator agents ---------------------
SEVERITY_LOW = "LOW"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_HIGH = "HIGH"

# Any failed rule at or above this severity triggers an escalation flag
# in the audit summary.
ESCALATION_THRESHOLD = SEVERITY_HIGH

# --- File paths -------------------------------------------------------------
DATA_DIR = "data"
OUTPUT_DIR = "outputs"
LEDGER_FILE = f"{DATA_DIR}/sample_ledger.csv"
MANDATES_FILE = f"{DATA_DIR}/sample_mandates.csv"
AUDIT_TRAIL_CSV = f"{OUTPUT_DIR}/audit_trail.csv"
AUDIT_TRAIL_JSON = f"{OUTPUT_DIR}/audit_trail.json"
AUDIT_SUMMARY_CSV = f"{OUTPUT_DIR}/audit_summary.csv"
