import os
import logging
from typing import Dict, Any, Optional

from pydantic import BaseModel

from agents.base_agent import BaseAgent
from utils.performance_metrics import estimate_tokens
from .types import MemorySummary, SummarizerInput


def _get_anthropic_llm():
    """Return a callable that invokes Claude Haiku, or None for mock mode.

    We prefer to avoid hard dependency; if Anthropic client isn't available,
    we run in mock mode and rely on tests to validate structure.
    """
    try:
        from anthropic import Anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None

        client = Anthropic(api_key=api_key)

        def call_llm(prompt: str) -> Dict[str, Any]:
            resp = client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
                max_tokens=1200,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )
            content = resp.content[0].text if getattr(resp, "content", None) else "{}"
            # We expect JSON; agent will validate
            try:
                import json

                return json.loads(content)
            except Exception:
                return {"user_confirmed": {}, "llm_inferred": {}, "general_summary": content}

        return call_llm
    except Exception:
        return None


class MemorySummarizerAgent(BaseAgent):
    """MCP-style agent that generates three-field chat memory summaries."""

    def __init__(self, mock: bool = False, logger: Optional[logging.Logger] = None):
        prompt = (
            "You are a summarization agent that produces a JSON object with exactly three fields: "
            "user_confirmed (object), llm_inferred (object), general_summary (string).\n\n"
            "Input provides prior memory and a new context snippet.\n"
            "Rules:\n"
            "- Preserve and update user_confirmed facts explicitly stated by the user.\n"
            "- Add model-derived assumptions under llm_inferred, never mixing them.\n"
            "- Produce a concise general_summary (<= 600 words).\n"
            "Output MUST be valid JSON matching the schema without extra keys.\n\n"
            "Prior memory (JSON):\n{prior_memory}\n\nNew context snippet:\n{new_context_snippet}\n\n"
            "Respond with ONLY the JSON object."
        )

        super().__init__(
            name="memory_summarizer",
            prompt=prompt,
            output_schema=MemorySummary,
            llm=_get_anthropic_llm(),
            mock=mock,
            logger=logger,
        )

    def format_prompt(self, user_input: str, **kwargs) -> str:
        # user_input is unused; we use kwargs for structured inputs
        prior_memory = kwargs.get("prior_memory", {})
        new_context_snippet = kwargs.get("new_context_snippet", "")
        import json

        return self.prompt.format(
            prior_memory=json.dumps(prior_memory, ensure_ascii=False),
            new_context_snippet=new_context_snippet,
        )

    def mock_output(self, user_input: str) -> BaseModel:
        # Provide realistic default structure
        return MemorySummary(
            user_confirmed={},
            llm_inferred={},
            general_summary="",
        )

    def summarize(self, prior_memory: Dict[str, Any], new_context_snippet: str) -> MemorySummary:
        output = self.__call__(
            user_input="",
            prior_memory=prior_memory,
            new_context_snippet=new_context_snippet,
        )
        # output is MemorySummary (validated)
        return output

    @staticmethod
    def count_tokens(summary: MemorySummary) -> int:
        # Simple heuristic for token counting
        return estimate_tokens(summary.model_dump_json())

