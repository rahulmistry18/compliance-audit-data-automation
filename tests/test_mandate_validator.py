import pandas as pd

from src.validators.mandate_validator import (
    TerminationAfterStartRule,
    MinimumNoticePeriodRule,
    StatusConsistencyRule,
    MandateValidatorAgent,
)


def base_row(**overrides):
    row = {
        "mandate_id": "MND-1",
        "client_name": "Client A",
        "start_date": pd.Timestamp("2020-01-01"),
        "termination_request_date": pd.Timestamp("2023-01-01"),
        "termination_date": pd.Timestamp("2023-02-01"),
        "status": "TERMINATED",
    }
    row.update(overrides)
    return row


def test_termination_after_start_pass():
    result = TerminationAfterStartRule().evaluate(base_row())
    assert result.status == "PASS"


def test_termination_after_start_fail():
    result = TerminationAfterStartRule().evaluate(base_row(
        termination_date=pd.Timestamp("2019-01-01")
    ))
    assert result.status == "FAIL"


def test_termination_after_start_not_applicable_when_no_termination():
    result = TerminationAfterStartRule().evaluate(base_row(termination_date=pd.NaT))
    assert result.status == "PASS"


def test_minimum_notice_period_pass():
    result = MinimumNoticePeriodRule().evaluate(base_row(
        termination_request_date=pd.Timestamp("2023-01-01"),
        termination_date=pd.Timestamp("2023-02-15"),  # 45 days
    ))
    assert result.status == "PASS"


def test_minimum_notice_period_fail_short_notice():
    result = MinimumNoticePeriodRule().evaluate(base_row(
        termination_request_date=pd.Timestamp("2023-01-01"),
        termination_date=pd.Timestamp("2023-01-10"),  # 9 days
    ))
    assert result.status == "FAIL"


def test_status_consistency_fail_unrecognised_status():
    result = StatusConsistencyRule().evaluate(base_row(status="SUSPENDED"))
    assert result.status == "FAIL"


def test_status_consistency_fail_active_but_terminated_date_passed():
    result = StatusConsistencyRule().evaluate(base_row(
        status="ACTIVE", termination_date=pd.Timestamp("2020-01-01")
    ))
    assert result.status == "FAIL"


def test_status_consistency_fail_terminated_without_date():
    result = StatusConsistencyRule().evaluate(base_row(
        status="TERMINATED", termination_date=pd.NaT
    ))
    assert result.status == "FAIL"


def test_status_consistency_pass_active_no_termination():
    result = StatusConsistencyRule().evaluate(base_row(
        status="ACTIVE", termination_date=pd.NaT, termination_request_date=pd.NaT
    ))
    assert result.status == "PASS"


def test_mandate_validator_agent_runs_all_rules_per_row():
    df = pd.DataFrame([base_row(), base_row(mandate_id="MND-2")])
    agent = MandateValidatorAgent(df)
    results = agent.run()
    # 3 rules x 2 rows
    assert len(results) == 6
