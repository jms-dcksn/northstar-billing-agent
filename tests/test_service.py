from datetime import timedelta

import pytest

from northstar.fixtures import AS_OF, scenario
from northstar.service import BillingRuleError, MockBillingAPI, eligibility


@pytest.mark.parametrize(
    "name,expected",
    [
        ("eligible", True),
        ("boundary", True),
        ("small", True),
        ("euro", False),
        ("seven_days", True),
        ("over_limit", False),
        ("old", False),
        ("refunded", False),
        ("ambiguous", False),
    ],
)
def test_policy(name, expected):
    case = scenario(name)
    result = eligibility(case, [c["charge_id"] for c in case["charges"]])
    assert result["eligible"] is expected
    assert result["charge_id"].endswith("_2")


def test_time_currency_and_status_boundaries():
    case = scenario("eligible")
    ids = [c["charge_id"] for c in case["charges"]]
    case["charges"][0]["settled_at"] = (AS_OF - timedelta(days=7, minutes=1)).isoformat()
    case["charges"][1]["settled_at"] = (AS_OF - timedelta(days=7, seconds=1)).isoformat()
    assert not eligibility(case, ids)["eligible"]
    for key, value in [("currency", "EUR"), ("status", "pending"), ("period", "2026-10")]:
        case = scenario("eligible")
        case["charges"][1][key] = value
        assert not eligibility(case, ids)["eligible"]


def test_approval_binding_and_account_isolation(tmp_path):
    api = MockBillingAPI(tmp_path / "db")
    case = api.open("a", "eligible")
    with pytest.raises(BillingRuleError):
        api.open("a", "over_limit")
    with pytest.raises(BillingRuleError):
        api.select("a", ["foreign_charge", "ch_eligible_2"])
    with pytest.raises(BillingRuleError):
        api.submit("a")
    api.select("a", [c["charge_id"] for c in case["charges"]])
    proposal = api.check("a")
    with pytest.raises(BillingRuleError):
        api.approve("a", "stale-proposal")
    api.approve("a", proposal["proposal_id"])
    api.mutate("a", lambda c: c["charges"][1].update(amount_cents=2100))
    with pytest.raises(BillingRuleError):
        api.submit("a")
    assert not api.get("a")["refunds"]
