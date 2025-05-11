"""
Dataset Snapshot

This script creates snapshots of datasets in LangSmith for versioning and evaluation.
"""

import os
import json
import argparse
from typing import Dict, Any, List
from langsmith import Client
from config.langsmith_config import get_langsmith_client
from tests.config.eval_config import get_dataset_path

def load_dataset(dataset_path: str) -> List[Dict[str, Any]]:
    """Load a dataset from a JSON file."""
    with open(dataset_path, "r") as f:
        return json.load(f)

def create_dataset_snapshot(
    agent_name: str,
    dataset_version: str,
    description: str = None
) -> Dict[str, Any]:
    """Create a snapshot of a dataset in LangSmith."""
    # Load dataset
    dataset_path = get_dataset_path(agent_name, dataset_version)
    dataset = load_dataset(dataset_path)
    
    # Initialize LangSmith client
    client = get_langsmith_client()
    
    # Create dataset snapshot
    snapshot = client.create_dataset(
        name=f"{agent_name}_v{dataset_version}",
        description=description or f"Dataset v{dataset_version} for {agent_name}",
        data=dataset
    )
    
    # Save snapshot metadata
    metadata = {
        "agent_name": agent_name,
        "dataset_version": dataset_version,
        "snapshot_id": snapshot.id,
        "created_at": snapshot.created_at.isoformat(),
        "description": description
    }
    
    output_path = os.path.join(
        "evaluations",
        agent_name,
        f"dataset_v{dataset_version}_snapshot.json"
    )
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    return metadata

def main():
    parser = argparse.ArgumentParser(description="Create dataset snapshots in LangSmith")
    parser.add_argument("agent_name", help="Name of the agent")
    parser.add_argument("dataset_version", help="Version of the dataset to snapshot")
    parser.add_argument(
        "--description",
        help="Description of the dataset snapshot"
    )
    
    args = parser.parse_args()
    
    metadata = create_dataset_snapshot(
        agent_name=args.agent_name,
        dataset_version=args.dataset_version,
        description=args.description
    )
    
    print(f"Dataset snapshot created with ID: {metadata['snapshot_id']}")
    print(f"Metadata saved to: {os.path.join('evaluations', args.agent_name, f'dataset_v{args.dataset_version}_snapshot.json')}")

if __name__ == "__main__":
    main() 