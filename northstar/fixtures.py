from copy import deepcopy
from datetime import UTC, datetime, timedelta

AS_OF = datetime(2026, 11, 3, 18, tzinfo=UTC)


def scenario(name: str) -> dict:
    """Return an isolated mock authenticated account and billing snapshot."""
    amounts = {
        "eligible": 1999,
        "boundary": 2500,
        "small": 100,
        "euro": 1299,
        "seven_days": 999,
        "ten_dollars": 1000,
        "over_limit": 3000,
        "old": 1999,
        "refunded": 1999,
        "ambiguous": 1999,
        "timeout_recovered": 1999,
        "timeout_exhausted": 1999,
    }
    amount = amounts[name]
    currency = "EUR" if name == "euro" else "USD"
    age = 8 if name == "old" else 7 if name == "seven_days" else 1
    charges = []
    for index in (1, 2):
        charges.append(
            {
                "charge_id": f"ch_{name}_{index}",
                "account_id": f"acct_{name}",
                "subscription_id": "sub_audio",
                "period": "2026-11",
                "currency": currency,
                "amount_cents": amount,
                "status": "settled",
                "settled_at": (AS_OF - timedelta(days=age, minutes=2 - index)).isoformat(),
            }
        )
    if name == "ambiguous":
        charges[1]["subscription_id"] = "sub_family"
    refunds = []
    if name == "refunded":
        refunds.append(
            {
                "refund_id": "rf_existing",
                "charge_id": charges[1]["charge_id"],
                "amount_cents": amount,
                "status": "completed",
                "currency": currency,
            }
        )
    return deepcopy(
        {
            "scenario": name,
            "user_id": f"user_{name}",
            "account_id": f"acct_{name}",
            "charges": charges,
            "refunds": refunds,
            "as_of": AS_OF.isoformat(),
            "selected": [],
            "proposal": None,
            "approval": None,
            "status": "open",
            "ticket": None,
            "attempts": 0,
            "requests": [],
            "feedback": None,
        }
    )
