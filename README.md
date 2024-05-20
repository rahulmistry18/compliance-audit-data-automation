# Compliance Audit Data Automation — PoC

**Agentic Python workflow for automated ledger validation and audit quality checks**, bridging accounting and data analytics. Implements rule-based governance supporting **EMIR** and **MiFID II** compliance frameworks with full audit traceability.

> Proof of concept developed at Rennes School of Business (Jun 2023). All data in this repo is **synthetic** and generated locally for demonstration purposes — no real client, trade, or mandate data is included.

**[→ View the live results dashboard](https://YOUR-GITHUB-USERNAME.github.io/compliance-audit-data-automation/)**
*(replace `YOUR-GITHUB-USERNAME` after you push — see [Publishing the dashboard](#publishing-the-dashboard) below)*

---

## What it does

The pipeline runs a small team of independent **validator agents** over a general ledger and a mandate register, each agent applying a set of deterministic compliance rules. Every check — pass or fail — is written to an immutable **audit trail** so results can be reproduced and traced back to the exact rule, record, and timestamp that produced them.

```
                ┌───────────────────┐
 sample_ledger  │                   │      ┌──────────────────────┐
   .csv ───────▶│   Data Loader     │─────▶│  Ledger Validator     │──┐
                │  (schema checks)  │      │  Agent (EMIR/MiFID II)│  │
 sample_mandates│                   │      └──────────────────────┘  │
   .csv ───────▶│                   │─────▶┌──────────────────────┐  │   ┌───────────────┐
                └───────────────────┘      │  Mandate Validator    │──┼──▶│  Audit Trail   │
                                            │  Agent (termination)  │  │   │  (CSV + JSON)  │
                                            └──────────────────────┘  │   └───────┬───────┘
                                                                       │           │
                                                                       ▼           ▼
                                                              ┌─────────────────────────┐
                                                              │  Audit Summary Report    │
                                                              │  (pass/fail, severity,   │
                                                              │   escalation flags)      │
                                                              └─────────────────────────┘
```

### Validator agents

| Agent | Rule domain | Example checks |
|---|---|---|
| `LedgerValidatorAgent` | Bookkeeping integrity + regulatory reporting | Debit/credit balance per entry, duplicate transaction IDs, missing/invalid counterparty LEI, T+1 EMIR trade-reporting deadline breach, MiFID II mandatory field completeness (instrument ID, timestamp, venue, price) |
| `MandateValidatorAgent` | Mandate lifecycle governance | Termination date logically after start date, minimum notice period respected, status field consistent with termination/effective dates, orphaned "active" mandates past their end date |

Each rule returns a structured `RuleResult` (rule id, entity id, status, severity, message). The orchestrator (`src/main.py`) runs every agent, aggregates results, assigns an **escalation flag** to any `HIGH` severity failure, and writes:

- `outputs/audit_trail.csv` — one row per rule evaluation (full traceability)
- `outputs/audit_trail.json` — same data, machine-readable
- `outputs/audit_summary.csv` — pass/fail counts and escalations per rule

This mirrors the kind of rule-engine + traceability layer used to complement heavier ETL tools (e.g. **Alteryx**) in a real compliance/audit pipeline, while keeping the rule logic itself transparent, testable, and version-controlled in Python.

---

## Project structure

```
compliance-audit-data-automation/
├── README.md
├── requirements.txt
├── LICENSE
├── generate_sample_data.py     # creates synthetic ledger & mandate CSVs
├── data/
│   ├── sample_ledger.csv
│   └── sample_mandates.csv
├── src/
│   ├── config.py                # thresholds, deadlines, notice periods
│   ├── data_loader.py           # CSV loading + schema validation
│   ├── audit_trail.py           # audit log writer (CSV/JSON)
│   ├── main.py                  # orchestrator / entry point
│   └── validators/
│       ├── compliance_rules.py  # RuleResult dataclass, base Rule class
│       ├── ledger_validator.py  # EMIR / MiFID II ledger checks
│       └── mandate_validator.py # mandate termination checks
├── outputs/                     # generated reports (git-ignored contents)
├── docs/
│   └── index.html                # static results dashboard (GitHub Pages)
└── tests/
    ├── test_ledger_validator.py
    ├── test_mandate_validator.py
    └── test_compliance_rules.py
```

## Getting started

```bash
git clone <your-repo-url>
cd compliance-audit-data-automation
python -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt

# 1. generate synthetic sample data (or drop your own CSVs in data/)
python generate_sample_data.py

# 2. run the full validation workflow
python -m src.main

# 3. run the test suite
pytest -v
```

Running `src.main` prints a console summary and writes the audit trail + summary report to `outputs/`.

## Publishing the dashboard

`docs/index.html` is a self-contained, static results dashboard (no build step, no server) — it's the page a portfolio link should point to. To get a live URL:

1. Push this repo to GitHub.
2. In the repo, go to **Settings → Pages**.
3. Under **Build and deployment**, set **Source** to `Deploy from a branch`, branch `main`, folder `/docs`, then **Save**.
4. GitHub publishes it at `https://<your-username>.github.io/<repo-name>/` within a minute or two — that's the link to put on your portfolio.

The dashboard currently displays the results from the bundled synthetic sample data. If you re-run the workflow on different data and want the dashboard to reflect it, update the `register` and `escalations` arrays near the bottom of `docs/index.html` with the new figures from `outputs/audit_summary.csv` and `outputs/audit_trail.csv`.

## Regulatory context (why these rules)

- **EMIR** (European Market Infrastructure Regulation) requires derivative trades to be reported to a trade repository, generally by **T+1**. `LedgerValidatorAgent` flags any ledger entry whose reporting timestamp falls outside that window.
- **MiFID II** transaction reporting (RTS 22) requires a defined set of fields (instrument identifier, execution timestamp, venue, price, counterparty LEI) to be populated and internally consistent. Missing/invalid fields are flagged as `HIGH` severity.
- **Mandate termination validation** reflects common internal-audit governance checks: a mandate cannot be terminated before it starts, termination must respect any contractual notice period, and status metadata must stay consistent with dates — inconsistencies here are a classic audit-quality finding.

This is a simplified, educational rule set intended to demonstrate the automation pattern — it is **not** a certified regulatory compliance tool.

## Tech stack

`Python` · `pandas` · `NumPy` · `pytest` — designed to sit alongside Alteryx-based ETL in a broader audit-data pipeline.

## License

MIT — see [LICENSE](LICENSE).
