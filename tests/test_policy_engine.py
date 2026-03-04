import pytest
import os
from validators.policy_engine import PolicyEngine


@pytest.fixture
def mock_policy_path(tmp_path):
    policy_content = """
global_limits:
  max_transaction_amount: 5000.0

risk_thresholds:
  allow: 20
  review: 50

actions:
  test_action:
    base_risk: 10
    restricted_account_types:
      - "Restricted"
"""
    p = tmp_path / "test_policy.yaml"
    p.write_text(policy_content)
    return str(p)


def test_policy_load(mock_policy_path):
    engine = PolicyEngine(mock_policy_path)
    assert engine.policy["global_limits"]["max_transaction_amount"] == 5000.0


def test_global_limit_block(mock_policy_path):
    engine = PolicyEngine(mock_policy_path)
    context = {"transaction_amount": 6000.0}
    decision, reason, score = engine.evaluate_intent("some_action", context)
    assert decision == "BLOCK"
    assert "exceeds global limit" in reason


def test_restricted_account_type(mock_policy_path):
    engine = PolicyEngine(mock_policy_path)
    context = {"account_type": "Restricted", "transaction_amount": 100.0}
    decision, reason, score = engine.evaluate_intent("test_action", context)
    assert decision == "BLOCK"
    assert "restricted for account type 'Restricted'" in reason


def test_allow_decision(mock_policy_path):
    engine = PolicyEngine(mock_policy_path)
    context = {"account_type": "Standard", "transaction_amount": 100.0}
    decision, reason, score = engine.evaluate_intent("test_action", context)
    assert decision == "ALLOW"
    assert score == 11  # base 10 + 1 (100/100)


def test_review_decision(mock_policy_path):
    engine = PolicyEngine(mock_policy_path)
    # Raising risk score to 35 (base 10 + 25)
    context = {"account_type": "Standard", "transaction_amount": 2500.0}
    decision, reason, score = engine.evaluate_intent("test_action", context)
    assert decision == "REVIEW"
    assert score == 35
