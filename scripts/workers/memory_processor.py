#!/usr/bin/env python3
import logging
import os
import time
from typing import Dict, Any

from agents.tooling.mcp.memory.summarizer_agent import MemorySummarizerAgent
from db.services.memory_service import get_memory_service, MemoryService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("memory_processor")


def process_once(memory_service: MemoryService, summarizer: MemorySummarizerAgent, token_limit: int) -> int:
    """Process up to N pending queue items once. Returns number processed."""
    pending = memory_service.get_pending_queue(limit=50)
    if not pending:
        return 0

    processed = 0
    for item in pending:
        queue_id = item.get("id")
        chat_id = item.get("chat_id")
        snippet = item.get("new_context_snippet", "")

        try:
            # Retrieve prior memory
            prior = memory_service.get_memory(chat_id)

            # Summarize
            summary = summarizer.summarize(prior_memory=prior, new_context_snippet=snippet)

            # Token management
            token_count = summarizer.count_tokens(summary)
            if token_count > token_limit:
                # Mark as complete but store a truncated general_summary with instruction
                truncated = summary.model_copy()
                truncated.general_summary = (
                    "Context exceeds size limit. Please start a new chat to continue."
                )
                memory_service.upsert_memory(
                    chat_id=chat_id,
                    user_confirmed=truncated.user_confirmed,
                    llm_inferred=truncated.llm_inferred,
                    general_summary=truncated.general_summary,
                    token_count=token_count,
                )
                memory_service.update_queue_status(queue_id, "complete")
                processed += 1
                continue

            # Persist
            memory_service.upsert_memory(
                chat_id=chat_id,
                user_confirmed=summary.user_confirmed,
                llm_inferred=summary.llm_inferred,
                general_summary=summary.general_summary,
                token_count=token_count,
            )
            memory_service.update_queue_status(queue_id, "complete")
            processed += 1

        except Exception as exc:
            logger.exception(f"Failed processing queue_id={queue_id} chat_id={chat_id}: {exc}")
            # Increment retry count and set error
            memory_service.update_queue_status(queue_id, "pending_summarization", error_message=str(exc), retry_increment=(item.get("retry_count", 0) + 1))

    return processed


def run_processor() -> None:
    memory_service = get_memory_service()
    summarizer = MemorySummarizerAgent(mock=os.getenv("USE_MOCK_LLM", "true").lower() == "true")
    token_limit = int(os.getenv("MEMORY_TOKEN_LIMIT", "8000"))

    idle_sleep = float(os.getenv("MEMORY_PROCESSOR_IDLE_SLEEP", "2.0"))

    logger.info("Memory processor started. Monitoring queue...")
    try:
        while True:
            processed = process_once(memory_service, summarizer, token_limit)
            if processed == 0:
                time.sleep(idle_sleep)
    except KeyboardInterrupt:
        logger.info("Processor exiting...")


if __name__ == "__main__":
    run_processor()