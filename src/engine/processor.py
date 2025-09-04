# engine/processors.py
"""
Message history processors for the Chronicle Engine.
These modify the conversation history before each LLM call to:
- Reduce token usage
- Summarize old messages
- Filter sensitive content
- Adapt based on runtime context (RunContext)

Designed for use with Pydantic AI's `Agent(history_processors=[...])`.
"""
from typing import List
from pydantic_ai.messages import ModelMessage
from pydantic_ai.tools import RunContext
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.ollama import OllamaProvider
import logging
import os

# --- Setup Logging ---
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())  # Prevents "no handler" warnings
if not logger.handlers:
    # Only add handler if running directly (e.g., for testing)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        )
    )
    logger.addHandler(handler)
    logger.setLevel(
        getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
    )

# --- Configurable Thresholds ---
SUMMARIZE_AFTER_MESSAGES = int(os.getenv("SUMMARIZE_AFTER_MESSAGES", "10"))
SUMMARIZE_AFTER_TOKENS = int(os.getenv("SUMMARIZE_AFTER_TOKENS", "1000"))
RECENT_MESSAGES_TO_KEEP = int(os.getenv("RECENT_MESSAGES_TO_KEEP", "4"))

# --- Small Model ---
small_model = OpenAIModel(
    'llama3.2',  # Using llama3 as the default model
    provider=OllamaProvider(base_url='http://localhost:11434/v1'),
)

# --- Summarization Agent ---
# Uses a cheaper model to summarize old messages
summarizer_agent = Agent(
    model=small_model,  # Cost-effective for summarization
    system_prompt="""
Summarize this game session briefly.
Focus on key events: who died, what was discovered, what quests are active.
Do not include small talk or minor actions.
Output in third person, past tense.
Keep it under 3 sentences.
"""
)

# --- Processor: Context-Aware Summarization ---
async def summarize_old_messages(
    ctx: RunContext[None],
    messages: List[ModelMessage]
) -> List[ModelMessage]:
    """
    If the conversation is long (in messages or tokens), summarize the oldest part
    and keep the most recent messages intact.

    Uses RunContext to access token usage and model info.
    """
    total_tokens = ctx.usage.total_tokens if hasattr(ctx, 'usage') and ctx.usage else 0
    model_name = getattr(ctx, 'model_name', "unknown")

    logger.info(
        f"summarize_old_messages: {len(messages)} messages, "
        f"{total_tokens} tokens, model={model_name}"
    )

    # Skip if not long enough
    if len(messages) <= SUMMARIZE_AFTER_MESSAGES:
        logger.debug("Skipping summarization: message count below threshold")
        return messages

    if total_tokens <= SUMMARIZE_AFTER_TOKENS:
        logger.debug("Skipping summarization: token count below threshold")
        return messages

    # Split: summarize first N, keep last M
    cutoff = max(6, SUMMARIZE_AFTER_MESSAGES - RECENT_MESSAGES_TO_KEEP)
    old_messages = messages[:cutoff]
    recent_messages = messages[-RECENT_MESSAGES_TO_KEEP:]

    logger.info(f"Summarizing {len(old_messages)} old messages...")

    try:
        summary_result = await summarizer_agent.run(message_history=old_messages)
        summary_msgs = summary_result.new_messages()

        logger.info("Summarization successful. Replacing old messages.")
        return summary_msgs + recent_messages

    except Exception as e:
        logger.error(f"Summarization failed: {e}. Falling back to keep recent messages.")
        # Fallback: just keep recent messages
        return messages[-(cutoff + RECENT_MESSAGES_TO_KEEP):]


# --- Processor: Keep Only Recent Messages ---
def keep_recent_messages(
    ctx: RunContext[None],
    messages: List[ModelMessage]
) -> List[ModelMessage]:
    """
    Simple fallback: keep only the last N messages.
    Does not use summarization.
    """
    n = int(os.getenv("RECENT_MESSAGE_LIMIT", "6"))
    if len(messages) <= n:
        return messages
    logger.info(f"Trimming history from {len(messages)} to {n} messages")
    return messages[-n:]


# --- Processor: Filter Sensitive Content ---
def filter_sensitive_messages(
    ctx: RunContext[None],
    messages: List[ModelMessage]
) -> List[ModelMessage]:
    """
    Remove messages containing sensitive keywords.
    Useful for evals, logging, or privacy-preserving modes.
    """
    blocked_keywords = [
        "classified", "burn notice", "kill order",
        "sleepers", "double agent", "execute"
    ]
    filtered = []
    removed_count = 0

    for msg in messages:
        content = " ".join(
            str(part.content) for part in getattr(msg, 'parts', []) if hasattr(part, 'content')
        ).lower()

        if any(kw in content for kw in blocked_keywords):
            logger.warning(f"Filtered message containing sensitive content: {content[:50]}...")
            removed_count += 1
        else:
            filtered.append(msg)

    if removed_count > 0:
        logger.info(f"Removed {removed_count} sensitive messages from history")

    return filtered


# --- Export Processors ---
# You can use any combination in your Agent
__all__ = [
    "summarize_old_messages",
    "keep_recent_messages",
    "filter_sensitive_messages",
]