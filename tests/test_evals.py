import json
from copy import deepcopy
from pathlib import Path

import pytest
from langchain.messages import AIMessage

from evals.scoring import score_case
from evals.target import run_case
from tests.helpers import ScriptedModel, call, script

EXAMPLES = json.loads((Path(__file__).parents[1] / "evals/dataset.json").read_text())


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda e: e["inputs"]["case_id"])
def test_eval_target_and_scorer_with_scripted_model(example):
    eligible = example["outputs"]["category"] == "eligible"
    model = (
        script(example["inputs"]["scenario_id"], finish=False)
        if eligible
        else ScriptedModel(
            responses=[
                call("handoff_to_human", reason="Specialist review"),
                AIMessage(content="Ticket created."),
            ]
        )
    )
    output = run_case(example["inputs"], model=model)
    score = score_case(output, example["outputs"])
    assert score["correct"]
    assert score["mistake_cost_usd"] == 0
    assert not score["high_impact"]


def test_costs_and_wrong_identity_are_not_free():
    reference = EXAMPLES[0]["outputs"]
    base = {
        "action": "deny",
        "user_id": reference["user_id"],
        "account_id": reference["account_id"],
    }
    assert score_case(base, reference)["mistake_cost_usd"] == 100
    base["action"] = "handoff"
    assert score_case(base, reference)["mistake_cost_usd"] == 50
    output = {**base, "action": "propose_refund", "proposal": deepcopy(reference["proposal"])}
    output["proposal"]["charge_id"] = "wrong_charge"
    score = score_case(output, reference)
    assert not score["correct"] and score["high_impact"] and score["mistake_cost_usd"] > 0
    ineligible = EXAMPLES[5]["outputs"]
    output.update(user_id=ineligible["user_id"], account_id=ineligible["account_id"])
    assert score_case(output, ineligible)["mistake_cost_usd"] == 19.99


def test_new_side_effect_on_previously_refunded_case_is_high_impact():
    reference = EXAMPLES[7]["outputs"]
    output = {
        "action": "handoff",
        "user_id": reference["user_id"],
        "account_id": reference["account_id"],
        "ticket": {
            "ticket_id": "NS-X",
            "user_id": reference["user_id"],
            "account_id": reference["account_id"],
        },
        "refunds": [{"refund_id": "rf_existing"}, {"refund_id": "rf_new"}],
    }
    assert score_case(output, reference)["high_impact"]
