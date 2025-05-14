"""
Run Evaluations

This script runs LangSmith evaluations for agents using specified prompts and datasets.
"""

import os
import json
import argparse
from typing import Dict, Any, List
from langsmith import Client
from langsmith.evaluation import evaluate
from config.langsmith_config import get_langsmith_client
from tests.config.eval_config import get_eval_config, get_dataset_path, get_evaluation_path

def load_dataset(dataset_path: str) -> List[Dict[str, Any]]:
    """Load a dataset from a JSON file."""
    with open(dataset_path, "r") as f:
        return json.load(f)

def run_evaluation(
    agent_name: str,
    prompt_version: str,
    dataset_version: str,
    custom_evaluators: List[str] = None
) -> Dict[str, Any]:
    """Run a LangSmith evaluation for an agent."""
    # Get evaluation configuration
    eval_config = get_eval_config(
        agent_name=agent_name,
        prompt_version=prompt_version,
        dataset_version=dataset_version,
        custom_evaluators=custom_evaluators
    )
    
    # Load dataset
    dataset_path = get_dataset_path(agent_name, dataset_version)
    dataset = load_dataset(dataset_path)
    
    # Initialize LangSmith client
    client = get_langsmith_client()
    
    # Run evaluation
    results = evaluate(
        dataset=dataset,
        evaluators=eval_config["evaluators"],
        metadata=eval_config["metadata"],
        client=client
    )
    
    # Save results
    output_path = get_evaluation_path(agent_name, prompt_version, dataset_version)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Run LangSmith evaluations")
    parser.add_argument("agent_name", help="Name of the agent to evaluate")
    parser.add_argument("prompt_version", help="Version of the prompt to use")
    parser.add_argument("dataset_version", help="Version of the dataset to use")
    parser.add_argument(
        "--evaluators",
        nargs="+",
        help="Additional evaluators to use"
    )
    
    args = parser.parse_args()
    
    results = run_evaluation(
        agent_name=args.agent_name,
        prompt_version=args.prompt_version,
        dataset_version=args.dataset_version,
        custom_evaluators=args.evaluators
    )
    
    print(f"Evaluation completed. Results saved to {get_evaluation_path(args.agent_name, args.prompt_version, args.dataset_version)}")
    print("\nSummary:")
    for evaluator, metrics in results.items():
        print(f"\n{evaluator}:")
        for metric, value in metrics.items():
            print(f"  {metric}: {value}")

if __name__ == "__main__":
    main() 