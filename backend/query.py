import logging
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.core.retrievers import AutoMergingRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from llama_index.core.postprocessor import SentenceTransformerRerank
from agents.rewrite_agent import rewrite_query

logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger(__name__)

Settings.llm = Ollama(
    model="llama3.2", request_timeout=120.0,
    context_window=4096, additional_kwargs={"num_ctx": 4096},
)
Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")

DOCSTORE_PATH = "storage"


def ask(question: str, collection_name: str = "documents") -> str:
    client = QdrantClient(url="http://localhost:6333")
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        enable_hybrid=True,
        fastembed_sparse_model="Qdrant/bm25",
    )

    docstore = SimpleDocumentStore.from_persist_dir(DOCSTORE_PATH)
    storage_context = StorageContext.from_defaults(docstore=docstore, vector_store=vector_store)

    index = VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context)

    base_retriever = index.as_retriever(
        similarity_top_k=20,          # cast a wide net -- cheap bi-encoder search
        vector_store_query_mode="hybrid",
        sparse_top_k=20,
    )

    retriever = AutoMergingRetriever(base_retriever, storage_context, verbose=True)

    # Cross-encoder reranker: re-scores the top-20 retrieved chunks against
    # the actual query, keeping only the 5 most genuinely relevant.
    # This is what filters out the junk (resume, boilerplate) you saw earlier.
    reranker = SentenceTransformerRerank(
        model="BAAI/bge-reranker-base",
        top_n=2,
    )

    query_engine = RetrieverQueryEngine.from_args(
        retriever,
        node_postprocessors=[reranker],
    )

    logger.info("Querying: %s", question)
    rewritten_question = rewrite_query(question)
    logger.info("Using rewritten query for retrieval: %s", rewritten_question)
    response = query_engine.query(rewritten_question)
    return response


if __name__ == "__main__":
    question = input("Ask a question about your document: ")
    answer = ask(question)
    print("\n--- Answer ---")
    print(answer)
