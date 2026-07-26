import logging
import os
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.core.retrievers import AutoMergingRetriever
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from ingestion.config import configure_settings
from memory.redis_memory import format_history_for_prompt, append_turn

from agents.state import RAGState
from agents.rewrite_agent import rewrite_query
configure_settings()   # must run BEFORE building _index below, or embed_model defaults to OpenAI
logger = logging.getLogger(__name__)

DOCSTORE_PATH = "storage"
COLLECTION_NAME = "documents"

# Built once, reused across every query -- these are relatively expensive
# to construct (model loading), so we don't want to recreate them per-request.

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
_client = QdrantClient(url=QDRANT_URL)
_vector_store = QdrantVectorStore(
    client=_client, collection_name=COLLECTION_NAME,
    enable_hybrid=True, fastembed_sparse_model="Qdrant/bm25",
)
_docstore = SimpleDocumentStore.from_persist_dir(DOCSTORE_PATH)
_storage_context = StorageContext.from_defaults(docstore=_docstore, vector_store=_vector_store)
_index = VectorStoreIndex.from_vector_store(_vector_store, storage_context=_storage_context)
_base_retriever = _index.as_retriever(
    similarity_top_k=20, vector_store_query_mode="hybrid", sparse_top_k=20,
)
_retriever = AutoMergingRetriever(_base_retriever, _storage_context, verbose=False)
_reranker = SentenceTransformerRerank(model="BAAI/bge-reranker-base", top_n=2)


def rewrite_node(state: RAGState) -> dict:
    history = format_history_for_prompt(state["session_id"])
    rewritten = rewrite_query(state["question"], history)
    return {"rewritten_question": rewritten}


def retrieve_node(state: RAGState) -> dict:
    """Node 2: hybrid search + parent-child merge."""
    nodes = _retriever.retrieve(state["rewritten_question"])
    logger.info("Retrieved %d node(s) after merge.", len(nodes))
    return {"retrieved_nodes": nodes}


def rerank_node(state: RAGState) -> dict:
    """Node 3: cross-encoder reranking down to the most relevant nodes."""
    from llama_index.core import QueryBundle
    reranked = _reranker.postprocess_nodes(
        state["retrieved_nodes"], QueryBundle(query_str=state["rewritten_question"])
    )
    logger.info("Reranked down to %d node(s).", len(reranked))
    return {"reranked_nodes": reranked}


def answer_node(state: RAGState) -> dict:
    """Node 4: generate the final answer using the reranked context."""
    context = "\n\n".join(n.node.get_content() for n in state["reranked_nodes"])
    prompt = (
        f"Answer the question using ONLY the context below. "
        f"If the context doesn't contain the answer, say so.\n\n"
        f"Context:\n{context}\n\nQuestion: {state['question']}\nAnswer:"
    )
    response = Settings.llm.complete(prompt)
    return {"answer": str(response)}

ROUTER_PROMPT = """Classify the user's message into exactly one category.

Categories:
- "retrieval": the message is a real question that likely needs information \
from documents to answer (facts, explanations, details about specific topics).
- "direct": the message is a greeting, thanks, small talk, or something that \
can be answered without looking anything up.

Respond with ONLY the category word, nothing else.

Message: {question}
Category:"""


def router_node(state: RAGState) -> dict:
    """Classifies the question to decide whether retrieval is needed."""
    prompt = ROUTER_PROMPT.format(question=state["question"])
    response = Settings.llm.complete(prompt)
    category = str(response).strip().lower()
    category = category.strip('"\'.,!')   # NEW: strip stray quotes/punctuation the model adds

    # Defensive fallback: if the model outputs something unexpected,
    # default to "retrieval" -- safer to over-retrieve than to wrongly
    # skip retrieval for a real question.
    if category not in ("retrieval", "direct"):
        logger.warning("Unexpected router output %r, defaulting to 'retrieval'.", category)
        category = "retrieval"

    logger.info("Routed question to: %s", category)
    return {"route": category}


def direct_answer_node(state: RAGState) -> dict:
    """Handles greetings/chitchat without touching the retrieval pipeline."""
    prompt = f"Respond briefly and naturally to this message: {state['question']}"
    response = Settings.llm.complete(prompt)
    return {"answer": str(response)}


def route_decision(state: RAGState) -> str:
    """Used by add_conditional_edges to pick the next node name."""
    return state["route"]

def citation_node(state: RAGState) -> dict:
    """
    Extracts a clean source reference from each reranked node's metadata.
    Handles both local files (file_name [+ page_label]) and websites (url),
    since they carry different metadata keys.
    """
    citations = []
    for scored_node in state["reranked_nodes"]:
        metadata = scored_node.node.metadata

        if "url" in metadata:
            source = metadata["url"]
        elif "file_name" in metadata:
            source = metadata["file_name"]
            if "page_label" in metadata:
                source += f" (page {metadata['page_label']})"
        else:
            source = "Unknown source"

        # Avoid duplicate citations if multiple chunks came from the same source.
        if source not in citations:
            citations.append(source)

    logger.info("Extracted %d citation(s): %s", len(citations), citations)
    return {"citations": citations}

def memory_save_node(state: RAGState) -> dict:
    """Persists this turn to Redis so future messages in this session have context."""
    append_turn(state["session_id"], state["question"], state["answer"])
    return {}