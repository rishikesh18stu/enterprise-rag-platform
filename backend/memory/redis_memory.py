import os
import json
import logging
import redis

logger = logging.getLogger(__name__)


REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
_client = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

MAX_TURNS = 6          # how many past exchanges to keep per session
TTL_SECONDS = 60 * 60 * 24   # sessions expire after 24h of inactivity


def _key(session_id: str) -> str:
    return f"chat_history:{session_id}"


def get_history(session_id: str) -> list[dict]:
    """Returns the list of {question, answer} turns for this session, oldest first."""
    raw = _client.get(_key(session_id))
    if raw is None:
        return []
    return json.loads(raw)


def append_turn(session_id: str, question: str, answer: str) -> None:
    """Adds a new turn to this session's history, trimming to MAX_TURNS."""
    history = get_history(session_id)
    history.append({"question": question, "answer": answer})
    history = history[-MAX_TURNS:]   # keep only the most recent turns

    _client.set(_key(session_id), json.dumps(history), ex=TTL_SECONDS)
    logger.info("Saved turn for session %s (%d turn(s) now stored).", session_id, len(history))


def format_history_for_prompt(session_id: str) -> str:
    """Renders history as readable text for the rewrite agent's prompt."""
    history = get_history(session_id)
    if not history:
        return "(none)"

    lines = []
    for turn in history:
        lines.append(f"User asked: {turn['question']}")
        lines.append(f"Assistant answered: {turn['answer']}")
    return "\n".join(lines)
