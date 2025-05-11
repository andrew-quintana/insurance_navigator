# Prompt Evaluation with LangSmith

This document describes how to use LangSmith for prompt evaluation and versioning in the insurance navigator project.

## Overview

The project uses LangSmith for:
1. Tracing agent runs
2. Versioning prompts and datasets
3. Evaluating agent performance
4. Comparing different prompt versions

## Setup

1. Set environment variables:
```bash
export LANGCHAIN_API_KEY="your_api_key"
export LANGCHAIN_PROJECT="insurance_navigator"
```

2. Install dependencies:
```bash
pip install langsmith langchain
```

## Directory Structure

```
/agents/
  /prompt_security_agent/
    logic.py              # Core agent logic
    prompt_v1.0.md        # Prompt version 1.0
    prompt_v1.1.md        # Prompt version 1.1
    changelog.md          # Version history
    /tests/               # Agent-specific tests

/datasets/
  /prompt_security/
    dataset_v1.0.json     # Test dataset version 1.0
    dataset_v1.1.json     # Test dataset version 1.1

/evaluations/
  /prompt_security/
    eval_prompt_v1.0_dataset_v1.0.json  # Evaluation results
    dataset_v1.0_snapshot.json          # Dataset snapshot metadata

/config/
  langsmith_config.py     # LangSmith configuration
  /tests/
    eval_config.py        # Evaluation configuration
```

## Usage

### 1. Creating Dataset Snapshots

To create a snapshot of a dataset in LangSmith:

```bash
python snapshot_dataset.py prompt_security 1.0 --description "Initial security test dataset"
```

This will:
- Load the dataset from `/datasets/prompt_security/dataset_v1.0.json`
- Create a snapshot in LangSmith
- Save metadata to `/evaluations/prompt_security/dataset_v1.0_snapshot.json`

### 2. Running Evaluations

To evaluate an agent with a specific prompt and dataset version:

```bash
python run_evals.py prompt_security 1.0 1.0 --evaluators qa embedding_distance
```

This will:
- Load the prompt from `/agents/prompt_security_agent/prompt_v1.0.md`
- Load the dataset from `/datasets/prompt_security/dataset_v1.0.json`
- Run evaluations using specified evaluators
- Save results to `/evaluations/prompt_security/eval_prompt_v1.0_dataset_v1.0.json`

### 3. Viewing Results

Evaluation results are stored in two places:
1. Local JSON files in `/evaluations/`
2. LangSmith web interface (https://smith.langchain.com)

The local files contain:
- Evaluation metrics
- Metadata (prompt version, dataset version, git commit)
- Timestamps
- Custom evaluator results

## Available Evaluators

### Default Evaluators
- `qa`: Question answering accuracy
- `embedding_distance`: Semantic similarity
- `cot_criteria`: Chain-of-thought reasoning quality

### Agent-Specific Evaluators
- `factual_consistency`: For healthcare guide
- `helpfulness`: For patient navigator

## Best Practices

1. **Version Control**
   - Keep prompt versions in separate files
   - Document changes in changelog.md
   - Use semantic versioning (MAJOR.MINOR.PATCH)

2. **Dataset Management**
   - Create snapshots before major changes
   - Include diverse test cases
   - Document dataset versions

3. **Evaluation**
   - Run evaluations on all prompt changes
   - Compare against previous versions
   - Use multiple evaluators
   - Check for regressions

4. **Tracing**
   - Use @traceable decorator on key functions
   - Include metadata in traces
   - Monitor performance metrics

## Example Workflow

1. Create new prompt version:
```bash
cp agents/prompt_security_agent/prompt_v1.0.md agents/prompt_security_agent/prompt_v1.1.md
# Edit prompt_v1.1.md
```

2. Update changelog:
```bash
# Edit agents/prompt_security_agent/changelog.md
```

3. Create dataset snapshot:
```bash
python snapshot_dataset.py prompt_security 1.0
```

4. Run evaluation:
```bash
python run_evals.py prompt_security 1.1 1.0
```

5. Compare results:
```bash
# View results in LangSmith web interface
# Check local evaluation files
```

## Troubleshooting

1. **Missing API Key**
   - Check LANGCHAIN_API_KEY environment variable
   - Verify LangSmith account access

2. **Dataset Loading Errors**
   - Verify dataset file exists
   - Check JSON format
   - Ensure correct version numbers

3. **Evaluation Failures**
   - Check evaluator compatibility
   - Verify prompt format
   - Review error logs

4. **Tracing Issues**
   - Check @traceable decorator usage
   - Verify metadata format
   - Check LangSmith connection 