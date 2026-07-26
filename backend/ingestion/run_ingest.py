import argparse
import logging

from ingestion.config import configure_settings
from ingestion.loaders import load_local_files, load_websites
from ingestion.pipeline import store_documents

logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest documents into the RAG knowledge base.")
    parser.add_argument("--data-dir", type=str, help="Directory of local files to ingest.")
    parser.add_argument("--urls", nargs="*", help="One or more website URLs to ingest.")
    args = parser.parse_args()

    configure_settings()

    documents = []
    if args.data_dir:
        logger.info("Loading local files from %s", args.data_dir)
        documents.extend(load_local_files(args.data_dir))
    if args.urls:
        logger.info("Loading %d website(s)", len(args.urls))
        documents.extend(load_websites(args.urls))

    if not documents:
        logger.error("No --data-dir or --urls provided. Nothing to ingest.")
        return

    store_documents(documents)


if __name__ == "__main__":
    main()