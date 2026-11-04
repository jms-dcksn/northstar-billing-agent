import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from northstar.fixtures import scenario


class BillingRuleError(ValueError):
    pass


def fingerprint(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:24]


def eligibility(case: dict, charge_ids: list[str]) -> dict:
    records = {c["charge_id"]: c for c in case["charges"]}
    if not charge_ids or len(set(charge_ids)) != len(charge_ids):
        raise BillingRuleError("Select distinct billing records first.")
    if any(cid not in records for cid in charge_ids):
        raise BillingRuleError("Charge does not belong to the authenticated account.")
    if len(charge_ids) != 2:
        return {"eligible": False, "reason": "Exactly two charges need human review."}
    earlier, later = sorted(
        [records[cid] for cid in charge_ids], key=lambda c: (c["settled_at"], c["charge_id"])
    )
    keys = ("account_id", "subscription_id", "period", "currency", "amount_cents")
    reason = None
    if any(c["account_id"] != case["account_id"] for c in (earlier, later)):
        raise BillingRuleError("Account mismatch.")
    if any(earlier[k] != later[k] for k in keys):
        reason = "The records do not establish a duplicate of the same subscription and period."
    elif earlier["status"] != "settled" or later["status"] != "settled":
        reason = "Both charges must be settled."
    elif earlier["settled_at"] == later["settled_at"]:
        reason = "Settlement order is ambiguous; a specialist must review it."
    elif later["currency"] != "USD":
        reason = "The $25 policy does not define a non-USD limit; a specialist must review it."
    elif not 0 < later["amount_cents"] <= 2500:
        reason = "The duplicate exceeds the automatic refund limit of $25."
    elif (
        not timedelta(0)
        <= (datetime.fromisoformat(case["as_of"]) - datetime.fromisoformat(later["settled_at"]))
        <= timedelta(days=7)
    ):
        reason = "The duplicate is outside the previous seven days."
    elif any(r["charge_id"] == later["charge_id"] for r in case["refunds"]):
        reason = "A refund already exists against this charge."
    return {
        "eligible": reason is None,
        "reason": reason or "Eligible settled duplicate.",
        "user_id": case["user_id"],
        "account_id": case["account_id"],
        "charge_ids": sorted(charge_ids),
        "charge_id": later["charge_id"],
        "kept_charge_id": earlier["charge_id"],
        "amount_cents": later["amount_cents"],
        "currency": later["currency"],
        "policy_version": "billing-v1",
    }


class MockBillingAPI:
    """SQLite stands in for independent account, billing and ticketing APIs."""

    def __init__(self, path: str | Path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS cases (thread TEXT PRIMARY KEY, body TEXT)")

    @contextmanager
    def connection(self):
        with sqlite3.connect(self.path, timeout=10) as conn:
            conn.execute("BEGIN IMMEDIATE")
            yield conn

    def open(self, thread: str, scenario_id: str) -> dict:
        with self.connection() as conn:
            row = conn.execute("SELECT body FROM cases WHERE thread=?", (thread,)).fetchone()
            if row:
                case = json.loads(row[0])
                if case["scenario"] != scenario_id:
                    raise BillingRuleError("Start a new chat to change demo identity.")
                return case
            case = scenario(scenario_id)
            conn.execute("INSERT INTO cases VALUES (?,?)", (thread, json.dumps(case)))
            return case

    def get(self, thread: str) -> dict:
        with self.connection() as conn:
            row = conn.execute("SELECT body FROM cases WHERE thread=?", (thread,)).fetchone()
            if row is None:
                raise BillingRuleError("No authenticated demo session.")
            return json.loads(row[0])

    def mutate(self, thread: str, operation):
        with self.connection() as conn:
            row = conn.execute("SELECT body FROM cases WHERE thread=?", (thread,)).fetchone()
            case = json.loads(row[0])
            result = operation(case)
            conn.execute("UPDATE cases SET body=? WHERE thread=?", (json.dumps(case), thread))
            return result

    def select(self, thread: str, charge_ids: list[str]):
        def update(case):
            eligibility(case, charge_ids)
            if sorted(case["selected"]) != sorted(charge_ids):
                case.update(selected=charge_ids, proposal=None, approval=None)
            return case["selected"]

        return self.mutate(thread, update)

    def check(self, thread: str) -> dict:
        def update(case):
            proposal = eligibility(case, case["selected"])
            proposal["proposal_id"] = fingerprint(proposal)
            if case["proposal"] != proposal:
                case["approval"] = None
            case["proposal"] = proposal
            case["status"] = "proposal" if proposal["eligible"] else "review_required"
            return proposal

        return self.mutate(thread, update)

    def approve(self, thread: str, proposal_id: str) -> dict:
        def update(case):
            proposal = case["proposal"]
            fresh = eligibility(case, case["selected"])
            fresh["proposal_id"] = fingerprint(fresh)
            if not proposal or fresh != proposal or not proposal["eligible"]:
                raise BillingRuleError("Eligibility changed; check and request a new approval.")
            if proposal_id != proposal["proposal_id"]:
                raise BillingRuleError("Approval does not match this exact refund proposal.")
            case["approval"] = dict(proposal)
            case["status"] = "approved"
            return case["approval"]

        return self.mutate(thread, update)

    def submit(self, thread: str) -> dict:
        def update(case):
            approval = case["approval"]
            if case["ticket"]:
                raise BillingRuleError("This case is with a specialist; do not submit again.")
            if not approval or approval != case["proposal"]:
                raise BillingRuleError("Explicit approval of the exact proposal is required.")
            key = f"refund-{thread}-{approval['proposal_id']}"
            existing = next((r for r in case["refunds"] if r.get("idempotency_key") == key), None)
            case["attempts"] += 1
            case["requests"].append({"idempotency_key": key, "approval": approval})
            if existing:
                return existing
            fresh = eligibility(case, case["selected"])
            fresh["proposal_id"] = fingerprint(fresh)
            if fresh != approval:
                raise BillingRuleError(
                    "Billing records changed; request new eligibility and approval."
                )
            if case["scenario"] == "timeout_exhausted":
                case["status"] = "submission_unknown"
                return {"timeout": True}
            refund = {
                "refund_id": f"rf_{fingerprint(key)}",
                "idempotency_key": key,
                "charge_id": approval["charge_id"],
                "amount_cents": approval["amount_cents"],
                "currency": approval["currency"],
                "status": "completed",
                "conversation_id": thread,
                "note": "Customer approved exact duplicate refund.",
            }
            case["refunds"].append(refund)
            case["status"] = "submitted"
            if case["scenario"] == "timeout_recovered" and case["attempts"] == 1:
                return {"timeout": True}
            return refund

        result = self.mutate(thread, update)
        if result.get("timeout"):
            raise TimeoutError("Mock billing POST timed out; outcome not yet confirmed.")
        return result

    def verify(self, thread: str) -> dict:
        def update(case):
            approval = case["approval"]
            if not approval:
                raise BillingRuleError("No approved refund to verify.")
            refund = next(
                (
                    r
                    for r in case["refunds"]
                    if r.get("idempotency_key") == f"refund-{thread}-{approval['proposal_id']}"
                    and r["status"] == "completed"
                ),
                None,
            )
            if not refund:
                raise BillingRuleError("Refund completion cannot be confirmed.")
            case["status"] = "completed"
            return refund

        return self.mutate(thread, update)

    def handoff(self, thread: str, reason: str) -> dict:
        def update(case):
            if not case["ticket"]:
                case["ticket"] = {
                    "ticket_id": f"NS-{fingerprint(thread)[:8].upper()}",
                    "reason": reason,
                    "user_id": case["user_id"],
                    "account_id": case["account_id"],
                    "conversation_id": thread,
                    "selected": case["selected"],
                    "proposal": case["proposal"],
                    "approval": case["approval"],
                    "submission_status": case["status"],
                    "requests": case["requests"],
                    "status": "awaiting_human_review",
                }
            case["status"] = "handoff"
            return case["ticket"]

        return self.mutate(thread, update)
