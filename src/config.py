"""
Central configuration for the compliance audit workflow.

Keeping thresholds and deadlines here (rather than hard-coded inside rules)
means the rule set can be re-tuned per jurisdiction/desk without touching
validator logic.

Reporting-deadline and data-field figures below reflect publicly available
regulatory text as of mid-2026 (EMIR REFIT / EMIR 3.0, MiFID III / MiFIR II,
the CFTC/SEC swap reporting rules under Dodd-Frank Title VII, and the
ASIC / HKMA-SFC / MAS post-2024 "rewrites" that align Asia-Pacific reporting
with the global CPMI-IOSCO Critical Data Elements standard). They are
simplified for teaching purposes and are NOT legal advice — see README for
sources and caveats.
"""

# --- Jurisdictions modelled in this PoC -----------------------------------
JURISDICTION_EU = "EU"
JURISDICTION_US = "US"
JURISDICTION_APAC = "APAC"

JURISDICTIONS = [JURISDICTION_EU, JURISDICTION_US, JURISDICTION_APAC]

# Human-readable label per jurisdiction: which regulator(s) and framework
# a ledger entry booked there is actually reported under.
JURISDICTION_LABELS = {
    JURISDICTION_EU: "EU — ESMA / EMIR & MiFID II",
    JURISDICTION_US: "US — CFTC / SEC (Dodd-Frank Title VII)",
    JURISDICTION_APAC: "APAC — ASIC / HKMA-SFC / MAS",
}

# --- Trade / transaction reporting deadlines --------------------------------
# Expressed in business days after execution ("T+N"). US swap reporting is
# "as soon as technologically practicable" under CFTC Parts 43/45, which in
# practice means same-day (T+0) — used here as the simplified same-day rule.
# EU EMIR REFIT kept the existing T+1 deadline. Asia-Pacific regulators
# (Australia's ASIC 2024 Rules, Hong Kong SFC/HKMA, Singapore MAS) moved
# from T+1 to a harmonised T+2 as part of their 2024–2025 rewrites.
REPORTING_DEADLINE_DAYS = {
    JURISDICTION_EU: 1,
    JURISDICTION_US: 0,
    JURISDICTION_APAC: 2,
}

# --- Critical Data Elements (CDE) -------------------------------------------
# CPMI-IOSCO's "Critical Data Elements" technical guidance is the common
# global standard behind MiFID II RTS 22 (EU), CFTC Parts 43/45 (US), and
# the ASIC/HKMA-SFC/MAS reporting rewrites (APAC) — all now converging on
# shared identifiers: LEI (counterparty), UPI (product), UTI (transaction).
# This PoC checks a simplified subset of those fields.
CDE_REQUIRED_FIELDS = [
    "instrument_id",
    "execution_timestamp",
    "venue",
    "price",
    "counterparty_lei",
]

# A Legal Entity Identifier is a 20-character alphanumeric code (ISO 17442),
# used identically across every jurisdiction modelled here.
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
