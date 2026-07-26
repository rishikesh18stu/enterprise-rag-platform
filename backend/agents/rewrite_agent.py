import logging
from llama_index.core.llms import ChatMessage
from llama_index.core import Settings


logger = logging.getLogger(__name__)

REWRITE_PROMPT_TEMPLATE = """Rewrite the QUESTION below into a clear, self-contained, \
full-sentence search query. Use the HISTORY only to resolve vague references \
like "it", "that", or "the thing".

Strict rules:
1. Output ONLY the rewritten question. No greetings, no explanations, no preamble.
2. If the question is already clear and self-contained, output it exactly as-is.
3. Never respond conversationally. You are not chatting -- you are transforming text.
4. If HISTORY is "(none)", ignore it and just clean up the QUESTION if needed.

HISTORY: {history}
QUESTION: {question}

REWRITTEN:"""


def rewrite_query(question: str, history: str = "(none)") -> str:
    """
    Uses the LLM to rewrite a possibly vague/context-dependent question
    into a clearer, standalone query better suited for retrieval.
    """
    prompt = REWRITE_PROMPT_TEMPLATE.format(history=history, question=question)

    response = Settings.llm.chat([ChatMessage(role="user", content=prompt)])
    rewritten = response.message.content.strip()

    logger.info("Original: %r -> Rewritten: %r", question, rewritten)
    return rewritten


if __name__ == "__main__":
    from llama_index.llms.ollama import Ollama
    Settings.llm = Ollama(
        model="llama3.2", request_timeout=120.0,
        context_window=4096, additional_kwargs={"num_ctx": 4096},
    )

    tests = [
        ("What is the capital of France?", "(none)"),
        ("what about the deadline thing", "User previously asked about the Q3 project timeline."),
        ("tell me more about that", "User previously asked: What is RAG?"),
    ]
    for question, history in tests:
        result = rewrite_query(question, history)
        print(f"\nOriginal:  {question}\nHistory:   {history}\nRewritten: {result}")
