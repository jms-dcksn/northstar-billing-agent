import json
import tempfile
from pathlib import Path
from uuid import uuid4

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from northstar.agent import DemoContext, build_agent
from northstar.service import MockBillingAPI


def extract(result: dict, case: dict) -> dict:
    """Normalize the observed create_agent state and LangGraph interrupt payload."""
    interrupts = result.get("__interrupt__", [])
    card = interrupts[0].value if interrupts else None
    proposal = card if card and card.get("kind") == "refund" else None
    if proposal:
        action = "propose_refund"
    elif case["ticket"]:
        action = "handoff"
    elif case["status"] == "review_required":
        action = "deny"
    else:
        action = "unresolved"
    return {
        "action": action,
        "proposal": proposal,
        "ticket": case["ticket"],
        "user_id": case["user_id"],
        "account_id": case["account_id"],
        "refunds": case["refunds"],
        "status": case["status"],
        "messages": [m.model_dump(mode="json") for m in result["messages"]],
    }


def run_case(inputs: dict, model=None) -> dict:
    """Evaluate the eligibility-to-proposal boundary; never approve or submit a refund."""
    with tempfile.TemporaryDirectory(prefix="northstar-eval-") as directory:
        api = MockBillingAPI(Path(directory) / "billing.sqlite")
        thread = f"eval-{uuid4()}"
        context = DemoContext(inputs["scenario_id"])
        case = api.open(thread, context.scenario_id)
        state = inputs["state"]
        if (state["user_id"], state["account_id"]) != (case["user_id"], case["account_id"]):
            raise ValueError("Dataset identity does not match its mock authenticated fixture.")
        api.select(thread, state["confirmed_charge_ids"])
        graph = build_agent(model=model, api=api, checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": thread}, "recursion_limit": 160}
        result = graph.invoke({"messages": inputs["messages"]}, config, context=context)
        # Allow a redundant charge-selection card, but never authorize a refund in this eval.
        for _ in range(2):
            interrupts = result.get("__interrupt__", [])
            if not interrupts or interrupts[0].value.get("kind") != "charges":
                break
            card = interrupts[0].value
            if sorted(c["charge_id"] for c in card["charges"]) != sorted(
                state["confirmed_charge_ids"]
            ):
                break
            result = graph.invoke(
                Command(resume={"action": "approve", "proposal_id": card["proposal_id"]}),
                config,
                context=context,
            )
        return extract(result, api.get(thread))


def save_result(directory: Path, example_id: str, output: dict):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{example_id}.json").write_text(json.dumps(output, indent=2))
