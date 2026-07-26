import uuid
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from auth.security import get_current_user
from agents.graph import build_graph
from agents.nodes import router_node, rewrite_node, retrieve_node, rerank_node, citation_node
from llama_index.core import Settings

router = APIRouter(prefix="/chat", tags=["chat"])

_graph = build_graph()


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    citations: list[str]
    session_id: str


def build_context_prompt(state: dict) -> str:
    context = "\n\n".join(n.node.get_content() for n in state["reranked_nodes"])
    return (
        f"Answer the question using ONLY the context below. "
        f"If the context doesn't contain the answer, say so.\n\n"
        f"Context:\n{context}\n\nQuestion: {state['question']}\nAnswer:"
    )


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, user: dict = Depends(get_current_user)):
    """Runs a question through the full LangGraph pipeline (non-streaming)."""
    session_id = payload.session_id or str(uuid.uuid4())
    result = _graph.invoke({"question": payload.question, "session_id": session_id})
    return ChatResponse(
        answer=result.get("answer", ""),
        citations=result.get("citations", []),
        session_id=session_id,
    )


@router.post("/stream")
def chat_stream(payload: ChatRequest, user: dict = Depends(get_current_user)):
    """Streams the answer token-by-token via Server-Sent Events."""
    session_id = payload.session_id or str(uuid.uuid4())
    state = {"question": payload.question, "session_id": session_id}

    state.update(router_node(state))

    if state["route"] == "direct":
        def direct_gen():
            response = Settings.llm.stream_complete(
                f"Respond briefly and naturally to this message: {state['question']}"
            )
            for chunk in response:
                yield f"data: {json.dumps({'token': chunk.delta})}\n\n"
            yield f"data: {json.dumps({'done': True, 'citations': [], 'session_id': session_id})}\n\n"

        return StreamingResponse(direct_gen(), media_type="text/event-stream")

    state.update(rewrite_node(state))
    state.update(retrieve_node(state))
    state.update(rerank_node(state))
    state.update(citation_node(state))

    def generate():
        prompt = build_context_prompt(state)
        full_answer = ""

        response_stream = Settings.llm.stream_complete(prompt)
        for chunk in response_stream:
            full_answer += chunk.delta
            yield f"data: {json.dumps({'token': chunk.delta})}\n\n"

        from memory.redis_memory import append_turn
        append_turn(session_id, payload.question, full_answer)

        yield f"data: {json.dumps({'done': True, 'citations': state['citations'], 'session_id': session_id})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/stats")
def chat_stats(user: dict = Depends(get_current_user)):
    """Basic usage analytics read live from Redis session data."""
    from memory.redis_memory import _client

    session_keys = _client.keys("chat_history:*")
    total_sessions = len(session_keys)
    total_messages = 0
    for key in session_keys:
        history = json.loads(_client.get(key))
        total_messages += len(history)

    return {"total_sessions": total_sessions, "total_messages": total_messages}
