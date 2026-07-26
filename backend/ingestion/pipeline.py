import os
import logging
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.node_parser import HierarchicalNodeParser, get_leaf_nodes
from llama_index.core.schema import Document
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)

CHUNK_SIZES = [1024, 256]
DOCSTORE_PATH = "storage"


def store_documents(documents: list[Document], collection_name: str = "documents") -> None:
    if not documents:
        logger.warning("No documents to store -- skipping.")
        return

    parser = HierarchicalNodeParser.from_defaults(chunk_sizes=CHUNK_SIZES)
    all_nodes = parser.get_nodes_from_documents(documents)
    leaf_nodes = get_leaf_nodes(all_nodes)

    logger.info(
        "Parsed %d total nodes (%d leaf/child nodes will be embedded).",
        len(all_nodes), len(leaf_nodes),
    )

    client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
    vector_store = QdrantVectorStore(
        client=client, collection_name=collection_name,
        enable_hybrid=True, fastembed_sparse_model="Qdrant/bm25",
    )

    # CRITICAL: load the EXISTING docstore if one is already persisted,
    # and add to it, instead of creating a fresh empty one. Overwriting
    # a fresh docstore on every ingestion call destroys previously
    # stored parent nodes -- exactly the bug that just crashed retrieval.
    if os.path.exists(DOCSTORE_PATH):
        docstore = SimpleDocumentStore.from_persist_dir(DOCSTORE_PATH)
        logger.info("Loaded existing docstore with %d doc(s).", len(docstore.docs))
    else:
        docstore = SimpleDocumentStore()

    docstore.add_documents(all_nodes)

    storage_context = StorageContext.from_defaults(
        docstore=docstore, vector_store=vector_store
    )

    VectorStoreIndex(leaf_nodes, storage_context=storage_context)
    storage_context.persist(persist_dir=DOCSTORE_PATH)

    logger.info(
        "Stored documents into collection '%s' (docstore now has %d total doc(s)).",
        collection_name, len(docstore.docs),
    )
