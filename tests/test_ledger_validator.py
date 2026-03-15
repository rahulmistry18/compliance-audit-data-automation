import pandas as pd
import pytest

from src.validators.ledger_validator import (
    DebitCreditBalanceRule,
    DuplicateTransactionRule,
    CounterpartyLEIRule,
    ReportingDeadlineRule,
    CDECompletenessRule,
    LedgerValidatorAgent,
)


def base_row(**overrides):
    row = {
        "transaction_id": "TXN-1",
        "jurisdiction": "EU",
        "trade_date": pd.Timestamp("2023-05-01"),
        "reporting_timestamp": pd.Timestamp("2023-05-02"),
        "counterparty_lei": "A" * 20,
        "instrument_id": "ISIN-DE0001234567",
        "execution_timestamp": pd.Timestamp("2023-05-01"),
        "venue": "XPAR",
        "price": 100.0,
        "debit": 1000.0,
        "credit": 0.0,
    }
    row.update(overrides)
    return row


def test_debit_credit_balance_pass():
    result = DebitCreditBalanceRule().evaluate(base_row())
    assert result.status == "PASS"


def test_debit_credit_balance_fail_both_populated():
    result = DebitCreditBalanceRule().evaluate(base_row(credit=500.0))
    assert result.status == "FAIL"
    assert result.severity == "HIGH"


def test_debit_credit_balance_fail_neither_populated():
    result = DebitCreditBalanceRule().evaluate(base_row(debit=0.0, credit=0.0))
    assert result.status == "FAIL"


def test_duplicate_transaction_rule():
    rule = DuplicateTransactionRule(duplicate_ids={"TXN-1"})
    result = rule.evaluate(base_row())
    assert result.status == "FAIL"

    rule_ok = DuplicateTransactionRule(duplicate_ids=set())
    result_ok = rule_ok.evaluate(base_row())
    assert result_ok.status == "PASS"


def test_counterparty_lei_rule_invalid_length():
    result = CounterpartyLEIRule().evaluate(base_row(counterparty_lei="TOO-SHORT"))
    assert result.status == "FAIL"


def test_counterparty_lei_rule_missing():
    result = CounterpartyLEIRule().evaluate(base_row(counterparty_lei=None))
    assert result.status == "FAIL"


# --- ReportingDeadlineRule: jurisdiction-aware --------------------------

def test_reporting_deadline_eu_pass_within_t1():
    result = ReportingDeadlineRule().evaluate(base_row(
        jurisdiction="EU",
        trade_date=pd.Timestamp("2023-05-01"),
        reporting_timestamp=pd.Timestamp("2023-05-02"),
    ))
    assert result.status == "PASS"
    assert "EU" in result.domain


def test_reporting_deadline_eu_fail_late():
    result = ReportingDeadlineRule().evaluate(base_row(
        jurisdiction="EU",
        trade_date=pd.Timestamp("2023-05-01"),
        reporting_timestamp=pd.Timestamp("2023-05-05"),
    ))
    assert result.status == "FAIL"
    assert result.severity == "HIGH"


def test_reporting_deadline_us_same_day_pass():
    result = ReportingDeadlineRule().evaluate(base_row(
        jurisdiction="US",
        trade_date=pd.Timestamp("2023-05-01"),
        reporting_timestamp=pd.Timestamp("2023-05-01"),
    ))
    assert result.status == "PASS"


def test_reporting_deadline_us_fail_next_day():
    result = ReportingDeadlineRule().evaluate(base_row(
        jurisdiction="US",
        trade_date=pd.Timestamp("2023-05-01"),
        reporting_timestamp=pd.Timestamp("2023-05-02"),
    ))
    assert result.status == "FAIL"


def test_reporting_deadline_apac_pass_within_t2():
    result = ReportingDeadlineRule().evaluate(base_row(
        jurisdiction="APAC",
        trade_date=pd.Timestamp("2023-05-01"),
        reporting_timestamp=pd.Timestamp("2023-05-03"),
    ))
    assert result.status == "PASS"


def test_reporting_deadline_apac_fail_after_t2():
    result = ReportingDeadlineRule().evaluate(base_row(
        jurisdiction="APAC",
        trade_date=pd.Timestamp("2023-05-01"),
        reporting_timestamp=pd.Timestamp("2023-05-05"),
    ))
    assert result.status == "FAIL"


def test_reporting_deadline_unrecognised_jurisdiction():
    result = ReportingDeadlineRule().evaluate(base_row(jurisdiction="MARS"))
    assert result.status == "FAIL"
    assert result.severity == "MEDIUM"


# --- CDECompletenessRule -------------------------------------------------

def test_cde_completeness_fail_missing_venue():
    result = CDECompletenessRule().evaluate(base_row(venue=""))
    assert result.status == "FAIL"
    assert "venue" in result.message


def test_cde_completeness_pass():
    result = CDECompletenessRule().evaluate(base_row())
    assert result.status == "PASS"


def test_ledger_validator_agent_runs_all_rules_per_row():
    df = pd.DataFrame([base_row(), base_row(transaction_id="TXN-2")])
    agent = LedgerValidatorAgent(df)
    results = agent.run()
    # 5 rules x 2 rows
    assert len(results) == 10
