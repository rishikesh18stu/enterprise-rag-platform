import os
from llama_index.core import Settings
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")


def configure_settings() -> None:
    Settings.llm = Ollama(
        model="llama3.2",
        base_url=OLLAMA_URL,
        request_timeout=300.0,
        context_window=4096,
        additional_kwargs={"num_ctx": 4096},
    )
    Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text", base_url=OLLAMA_URL)