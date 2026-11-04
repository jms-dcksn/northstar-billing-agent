import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DATASET_NAME = "northstar-refund-proposals-v1"


def main():
    parser = argparse.ArgumentParser(description="Manual Northstar dataset and experiment commands")
    parser.add_argument("command", choices=["validate", "upload", "run"])
    parser.add_argument("--dataset", default=DATASET_NAME)
    parser.add_argument("--prefix", default="northstar-sonnet")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")
    examples = json.loads((ROOT / "evals/dataset.json").read_text())
    if args.command == "validate":
        assert len(examples) == 10
        categories = [e["outputs"]["category"] for e in examples]
        assert {c: categories.count(c) for c in set(categories)} == {
            "eligible": 5,
            "ineligible": 3,
            "off_topic": 2,
        }
        print("10 examples: 5 eligible, 3 ineligible, 2 off-topic. No network calls.")
        return
    if not os.getenv("LANGSMITH_API_KEY") or not os.getenv("LANGSMITH_PROJECT"):
        parser.error("Set LANGSMITH_API_KEY and LANGSMITH_PROJECT in .env first.")
    from langsmith import Client

    client = Client()
    if args.command == "upload":
        if client.has_dataset(dataset_name=args.dataset):
            remote = list(client.list_examples(dataset_name=args.dataset))
            remote_pairs = sorted(json.dumps([e.inputs, e.outputs], sort_keys=True) for e in remote)
            local_pairs = sorted(
                json.dumps([e["inputs"], e["outputs"]], sort_keys=True) for e in examples
            )
            if remote_pairs != local_pairs:
                parser.error(
                    "Existing dataset differs. Use a new --dataset name; nothing overwritten."
                )
            print(f"Dataset already matches: {args.dataset} ({len(remote)} examples).")
            return
        dataset = client.create_dataset(
            args.dataset, description="Northstar eligibility-to-proposal: 5/3/2; mock data only."
        )
        client.create_examples(dataset_id=dataset.id, examples=examples)
        print(f"Created {dataset.name}: {len(examples)} examples. No experiments run.")
        return
    from evals.scoring import correctness, high_impact, mistake_cost_usd, total_mistake_cost
    from evals.target import run_case, save_result

    dataset = client.read_dataset(dataset_name=args.dataset)
    directory = ROOT / "evals/results" / args.prefix

    def target(inputs):
        output = run_case(inputs)
        save_result(directory, inputs["case_id"], output)
        return output

    results = client.evaluate(
        target,
        data=dataset.id,
        evaluators=[correctness, mistake_cost_usd, high_impact],
        summary_evaluators=[total_mistake_cost],
        max_concurrency=1,
        experiment_prefix=args.prefix,
        metadata={
            "model": os.getenv("NORTHSTAR_MODEL", "claude-sonnet-4-6"),
            "boundary": "eligibility_to_proposal",
            "policy": "billing-v1",
        },
    )
    list(results)
    print(f"Experiment: {results.experiment_name}; outputs: {directory}")


if __name__ == "__main__":
    main()
