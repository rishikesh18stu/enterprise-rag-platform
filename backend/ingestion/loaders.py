import logging
import requests
from bs4 import BeautifulSoup
from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import Document

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "EnterpriseRAG-LearningProject/1.0 (educational use; contact: your-email@example.com)"
}


def load_local_files(data_dir: str) -> list[Document]:
    """Loads PDF, DOCX, PPTX, XLSX, TXT, MD files from a directory."""
    return SimpleDirectoryReader(data_dir).load_data()


def load_websites(urls: list[str]) -> list[Document]:
    """
    Fetches and cleans text content from a list of URLs, using a proper
    User-Agent header (many sites silently block/stub requests without one).
    """
    documents = []
    for url in urls:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)

        if len(text) < 500:
            logger.warning(
                "Suspiciously short content (%d chars) fetched from %s. "
                "First 200 chars: %r", len(text), url, text[:200],
            )

        documents.append(Document(text=text, metadata={"url": url}))
        logger.info("Fetched %d characters from %s", len(text), url)

    return documents