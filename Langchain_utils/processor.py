"""
Unified processor module.

Combines memory, intent detection, and chain routing.
"""

from typing import Any, AsyncGenerator, Callable, Dict
import logging

from .memory import create_memory, format_chat_history
from .intent import detect_intent
from .chains import create_knowledge_chain, create_general_chain
from .config import DEFAULT_SESSION_ID


logger = logging.getLogger(__name__)


def create_unified_processor(
    system_prompt: str = "你是一个智能助手，可以根据需要查询知识库或直接回答用户问题。",
    session_id: str = DEFAULT_SESSION_ID,
) -> Callable[[str], AsyncGenerator[Dict[str, Any], None]]:
    """
    Create a unified processor function for one session.
    """
    memory = create_memory(session_id=session_id)
    knowledge_chain = create_knowledge_chain(system_prompt=system_prompt)
    general_chain = create_general_chain(system_prompt=system_prompt)

    stats: Dict[str, int] = {
        "total": 0,
        "knowledge_base": 0,
        "general_chat": 0,
    }

    async def processor(question: str) -> AsyncGenerator[Dict[str, Any], None]:
        stats["total"] += 1

        # Build history text for intent detection and chain prompts.
        messages = memory.chat_memory.messages
        history_text = format_chat_history(messages)

        intent = detect_intent(question, history_text)
        if intent == "knowledge_base":
            chain = knowledge_chain
            stats["knowledge_base"] += 1
        else:
            chain = general_chain
            stats["general_chat"] += 1

        logger.info("session=%s intent=%s question=%s", session_id, intent, question[:80])

        full_answer = ""
        yield {
            "type": "metadata",
            "data": {
                "intent": intent,
                "session_id": session_id,
            },
        }

        async for chunk in chain(question, history_text):
            full_answer += chunk
            yield {"type": "content", "data": chunk}

        # Persist conversation turn.
        memory.chat_memory.add_user_message(question)
        memory.chat_memory.add_ai_message(full_answer)

        yield {
            "type": "end",
            "data": {
                "metadata": {
                    "intent": intent,
                    "session_id": session_id,
                    "answer_length": len(full_answer),
                }
            },
        }

    def get_stats() -> Dict[str, int]:
        return dict(stats)

    def clear_memory() -> None:
        memory.clear()

    # Expose helper methods on the callable processor instance.
    processor.get_stats = get_stats  # type: ignore[attr-defined]
    processor.clear_memory = clear_memory  # type: ignore[attr-defined]

    return processor

