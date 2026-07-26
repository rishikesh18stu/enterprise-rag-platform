import logging
from agents.nodes import (
    router_node, direct_answer_node,
    rewrite_node, retrieve_node, rerank_node, answer_node,
    route_decision, citation_node, memory_save_node,
)
from langgraph.graph import StateGraph, START, END

from agents.state import RAGState


logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger(__name__)


def build_graph():
    builder = StateGraph(RAGState)

    builder.add_node("router", router_node)
    builder.add_node("memory_save", memory_save_node)
    builder.add_node("direct_answer", direct_answer_node)
    builder.add_node("rewrite", rewrite_node)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("rerank", rerank_node)
    builder.add_node("citation", citation_node)
    builder.add_node("answer", answer_node)

    builder.add_edge(START, "router")

    # Conditional edge: after router runs, route_decision() reads
    # state["route"] and returns either "retrieval" or "direct" --
    # LangGraph uses that string to pick which node runs next, based
    # on the mapping dict below.
    builder.add_conditional_edges(
        "router",
        route_decision,
        {
            "retrieval": "rewrite",
            "direct": "direct_answer",
        },
    )

    builder.add_edge("rewrite", "retrieve")
    builder.add_edge("retrieve", "rerank")
    builder.add_edge("rerank", "citation")
    builder.add_edge("citation", "answer")   # replaces the old "rerank" -> "answer" edge
    builder.add_edge("answer", "memory_save")
    builder.add_edge("direct_answer", "memory_save")
    builder.add_edge("memory_save", END)

    return builder.compile()



if __name__ == "__main__":
    from llama_index.core import Settings
    from llama_index.llms.ollama import Ollama
    from llama_index.embeddings.ollama import OllamaEmbedding

    # Settings.llm = Ollama(
    #     model="llama3.2", request_timeout=120.0,
    #     context_window=4096, additional_kwargs={"num_ctx": 4096},
    # )
    # Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")

    graph = build_graph()
    question = input("Ask a question: ")

    result = graph.invoke({"question": question, "session_id": "test-session-1"})

    print("\n--- Answer ---")
    print(result["answer"])
    print("\n--- Sources ---")
    for c in result.get("citations", []):
        print(f"- {c}")
