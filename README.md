# Compliance Audit Data Automation - PoC

Built by Rahul Mistari

Agentic Python workflow for automated ledger validation and audit quality checks, bridging accounting and data analytics. Implements rule-based governance spanning EU (EMIR / MiFID II), US (Dodd-Frank / CFTC / SEC), and Asia-Pacific (ASIC / HKMA-SFC / MAS) trade-reporting frameworks, with full audit traceability.

Proof of concept originally developed at Rennes School of Business (Jun 2023), later extended to cover multiple jurisdictions. All data in this repo is synthetic and generated locally for demonstration purposes; no real client, trade, or mandate data is included.

Live results dashboard: https://YOUR-GITHUB-USERNAME.github.io/compliance-audit-data-automation/
(replace `YOUR-GITHUB-USERNAME` after you push; see "Publishing the dashboard" below)

---

## What it does

The pipeline runs a small team of independent validator agents over a general ledger and a mandate register, each agent applying a set of deterministic compliance rules. Every check, pass or fail, is written to an immutable audit trail so results can be reproduced and traced back to the exact rule, record, and timestamp that produced them.

The flow is straightforward:

1. `sample_ledger.csv` and `sample_mandates.csv` are loaded and schema-checked by the data loader.
2. `LedgerValidatorAgent` runs its rule set (bookkeeping integrity, jurisdiction-aware reporting deadlines, data-field completeness) over every ledger row.
3. `MandateValidatorAgent` runs its rule set (termination logic, notice period, status consistency) over every mandate row.
4. Every rule evaluation from both agents is collected into a single audit trail and written to `outputs/` as CSV and JSON, plus a rule-level summary.

### Validator agents

| Agent | Rule domain | Example checks |
|---|---|---|
| `LedgerValidatorAgent` | Bookkeeping integrity and multi-jurisdiction regulatory reporting | Debit/credit balance per entry, duplicate transaction IDs, missing or invalid counterparty LEI, jurisdiction-aware trade-reporting deadline (EU T+1, US same-day, APAC T+2), Critical Data Element (CDE) field completeness (instrument ID, timestamp, venue, price) |
| `MandateValidatorAgent` | Mandate lifecycle governance | Termination date logically after start date, minimum notice period respected, status field consistent with termination and effective dates, orphaned "active" mandates past their end date |

Each ledger entry carries a `jurisdiction` field (`EU`, `US`, or `APAC`). The reporting-deadline and data-completeness rules read that field and apply the actual deadline and regulator label for that region, so the same rule engine produces an EMIR finding, a Dodd-Frank finding, or an ASIC finding depending on where the trade was booked, instead of hard-coding one regime.

Each rule returns a structured `RuleResult` (rule id, entity id, status, severity, message, domain, which includes the jurisdiction and regulator). The orchestrator (`src/main.py`) runs every agent, aggregates results, assigns an escalation flag to any HIGH severity failure, and writes:

- `outputs/audit_trail.csv`: one row per rule evaluation, full traceability
- `outputs/audit_trail.json`: same data, machine-readable
- `outputs/audit_summary.csv`: pass/fail counts and escalations per rule

This mirrors the kind of rule-engine and traceability layer used to complement heavier ETL tools (e.g. Alteryx) in a real compliance/audit pipeline, while keeping the rule logic itself transparent, testable, and version-controlled in Python.

---

## Project structure

```
compliance-audit-data-automation/
  README.md
  requirements.txt
  LICENSE
  generate_sample_data.py     creates synthetic ledger and mandate CSVs
  data/
    sample_ledger.csv
    sample_mandates.csv
  src/
    config.py                 thresholds, deadlines, notice periods
    data_loader.py             CSV loading and schema validation
    audit_trail.py             audit log writer (CSV/JSON)
    main.py                    orchestrator / entry point
    validators/
      compliance_rules.py      RuleResult dataclass, base Rule class
      ledger_validator.py      EU/US/APAC reporting and bookkeeping checks
      mandate_validator.py     mandate termination checks
  outputs/                     generated reports (git-ignored contents)
  docs/
    index.html                 static results dashboard (GitHub Pages)
  tests/
    test_ledger_validator.py
    test_mandate_validator.py
    test_compliance_rules.py
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

Running `src.main` prints a console summary and writes the audit trail and summary report to `outputs/`.

## Publishing the dashboard

`docs/index.html` is a self-contained, static results dashboard with no build step and no server; it's the page a portfolio link should point to. To get a live URL:

1. Push this repo to GitHub.
2. In the repo, go to Settings, then Pages.
3. Under "Build and deployment", set Source to "Deploy from a branch", branch `main`, folder `/docs`, then Save.
4. GitHub publishes it at `https://<your-username>.github.io/<repo-name>/` within a minute or two; that's the link to put on your portfolio.

The dashboard currently displays the results from the bundled synthetic sample data. If you re-run the workflow on different data and want the dashboard to reflect it, update the `register` and `escalations` arrays near the bottom of `docs/index.html` with the new figures from `outputs/audit_summary.csv` and `outputs/audit_trail.csv`.

## Understanding EMIR and MiFID II, in plain language

Both rules come out of the same place: after the 2008 financial crisis, regulators realized nobody had a clear picture of how much risk was building up in derivatives markets, or whether trading was happening fairly and transparently. The EU's response was two regulations that do different jobs.

EMIR (European Market Infrastructure Regulation): tell the regulator every derivative trade exists. Think of it as a radar system. Every time a bank, fund, or company trades a derivative (a contract whose value depends on something else, such as an interest rate, a currency, or a commodity), EMIR requires that trade to be reported to an approved trade repository, generally by the next business day. Regulators use this to see risk concentrations building up across the whole market, rather than waiting for a crisis to reveal them.

MiFID II (Markets in Financial Instruments Directive II): trade fairly, transparently, and keep proper records, for almost everything, not just derivatives. It's the EU's much broader rulebook for how financial markets operate: what must be disclosed about a trade (price, timing, venue, counterparty), best-execution obligations (firms must get clients a fair deal, not just a convenient one), and market transparency rules. This project checks a simplified slice of MiFID II's transaction-reporting requirement (RTS 22): a defined set of fields, instrument ID, timestamp, venue, price, and counterparty LEI, must be complete and correct.

In short: EMIR asks whether the regulator knows a given derivative trade happened. MiFID II asks whether that trade was conducted properly and is fully documented.

## Global regulatory landscape (2024-2026)

Trade-reporting rules aren't EU-only; the US and Asia-Pacific run their own regimes, and all of them have been actively rewritten in the last two years. This project models that directly: each ledger entry carries a `jurisdiction` (`EU`, `US`, or `APAC`), and the reporting-deadline rule applies the correct regime for that row.

| Region | Regulator(s) | Framework | Reporting deadline | What's changed recently |
|---|---|---|---|---|
| EU | ESMA | EMIR (REFIT) plus MiFID II / MiFIR | T+1 | EMIR REFIT's revised reporting standards took effect April 2024. EMIR 3.0's "Active Account Requirement" (reducing reliance on non-EU clearing houses) has been in force since December 2024, with technical standards entering force February 2026 and first compliance reports due July 2026. MiFID III / MiFIR II's transparency reforms, including a ban on payment-for-order-flow and a new EU consolidated tape, are phasing in through 2026-2027. |
| UK | FCA / Bank of England | UK EMIR (separate regime since Brexit) | T+1 | UK EMIR Refit implementation completed March 2025; further reporting-field amendments took effect January 2026. |
| US | CFTC (swaps) and SEC (security-based swaps) | Dodd-Frank Title VII, CFTC Parts 43/45, SEC Regulation SBSR | Same-day ("as soon as technologically practicable") | The SEC and CFTC, which have run separate, sometimes conflicting reporting regimes since Dodd-Frank split oversight between them, signed a Joint Harmonization Initiative MOU in March 2026 and opened a joint public comment period (June-August 2026) to align the two frameworks. |
| Australia | ASIC | Derivative Transaction Rules 2024 | T+2 (was T+1) | The 2024 Rules pushed the deadline from T+1 out to T+2 specifically to align with the rest of Asia-Pacific; further scope changes affecting foreign firms took effect October 2025. |
| Hong Kong | HKMA / SFC | OTC derivatives reporting regime | T+2 | Mandatory Unique Transaction Identifiers (UTI) and Unique Product Identifiers (UPI) from September 2025, standardizing the data fields reported ("Critical Data Elements") in line with the global standard below. |
| Singapore | MAS | Securities and Futures Act derivatives reporting | T+2 | Rewritten to adopt the same global UTI/UPI/CDE data standard as Australia, Hong Kong, and Japan. |

The pattern worth noticing: the deadlines differ (the US wants near-real-time visibility into the world's largest derivatives market, the EU sits at T+1, Asia-Pacific regulators deliberately relaxed to T+2 to ease implementation), but since 2024-2025 every one of these regimes has converged on the same underlying data standard: Unique Transaction Identifiers (UTI), Unique Product Identifiers (UPI), and Critical Data Elements (CDE), set by the international standard-setters CPMI and IOSCO. That convergence is what `CDECompletenessRule` in this codebase reflects: the same five fields (instrument ID, timestamp, venue, price, LEI) are checked regardless of jurisdiction, because that is genuinely where global practice has landed.

Figures above are simplified for teaching purposes and reflect publicly available regulatory guidance as of mid-2026 (ESMA, the UK FCA/Bank of England, the US CFTC/SEC, ASIC, HKMA/SFC, and MAS). This is not legal advice; always check current primary regulatory text before relying on any deadline or field list operationally.

## Regulatory context (why these rules)

- EMIR, MiFID II, Dodd-Frank, ASIC, HKMA-SFC, and MAS all require derivative trades to be reported to an approved repository within a set window. `ReportingDeadlineRule` reads each ledger entry's `jurisdiction` and flags any entry reported outside that region's deadline.
- Critical Data Elements (CDE) are the shared field set (instrument identifier, execution timestamp, venue, price, counterparty LEI) that EU, US, and APAC reporting regimes have all converged on. Missing or invalid fields are flagged as HIGH severity by `CDECompletenessRule`.
- Legal Entity Identifiers (LEI) are a single 20-character ISO 17442 code used identically to identify counterparties in every jurisdiction modelled here, checked by `CounterpartyLEIRule`.
- Mandate termination validation reflects common internal-audit governance checks, independent of jurisdiction: a mandate cannot be terminated before it starts, termination must respect any contractual notice period, and status metadata must stay consistent with dates. Inconsistencies here are a classic audit-quality finding.

This is a simplified, educational rule set intended to demonstrate the automation pattern. It is not a certified regulatory compliance tool.

## Tech stack

Python, Pandas, NumPy, pytest. Designed to sit alongside Alteryx-based ETL in a broader audit-data pipeline.

## Author

Built by Rahul Mistari.

## License

MIT. See [LICENSE](LICENSE).
