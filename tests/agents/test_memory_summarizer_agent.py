import os
import pytest

from agents.tooling.mcp.memory.summarizer_agent import MemorySummarizerAgent
from agents.tooling.mcp.memory.types import MemorySummary


@pytest.mark.unit
def test_summarizer_mock_output_structure():
    agent = MemorySummarizerAgent(mock=True)
    prior = {"user_confirmed": {"zip": "94110"}, "llm_inferred": {}, "general_summary": "prev"}
    out: MemorySummary = agent.summarize(prior_memory=prior, new_context_snippet="User confirms budget under $500.")

    assert isinstance(out, MemorySummary)
    assert hasattr(out, "user_confirmed")
    assert hasattr(out, "llm_inferred")
    assert hasattr(out, "general_summary")


@pytest.mark.unit
def test_token_counting_estimate():
    agent = MemorySummarizerAgent(mock=True)
    summary = MemorySummary(
        user_confirmed={"budget": "under_500"},
        llm_inferred={"urgency": "high"},
        general_summary="A short summary",
    )
    count = agent.count_tokens(summary)
    assert isinstance(count, int)
    assert count >= 0

