from src.validators.compliance_rules import Rule, RuleResult


def test_rule_result_autotimestamp():
    result = RuleResult(
        rule_id="TEST-001",
        domain="Test",
        entity_type="thing",
        entity_id="1",
        status="PASS",
        severity="LOW",
        message="ok",
    )
    assert result.evaluated_at != ""


def test_rule_pass_helper():
    class DummyRule(Rule):
        rule_id = "DUMMY-001"
        domain = "Test"
        entity_type = "thing"

        def evaluate(self, record):
            return self._pass(record["id"])

    result = DummyRule().evaluate({"id": "abc"})
    assert result.status == "PASS"
    assert result.entity_id == "abc"


def test_rule_fail_helper():
    class DummyRule(Rule):
        rule_id = "DUMMY-002"
        domain = "Test"
        entity_type = "thing"

        def evaluate(self, record):
            return self._fail(record["id"], "HIGH", "bad")

    result = DummyRule().evaluate({"id": "xyz"})
    assert result.status == "FAIL"
    assert result.severity == "HIGH"
    assert result.message == "bad"
