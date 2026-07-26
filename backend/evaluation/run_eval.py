import logging
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from ragas.llms import LlamaIndexLLMWrapper
from ragas.embeddings import LlamaIndexEmbeddingsWrapper
from llama_index.core import Settings

from ingestion.config import configure_settings
from agents.nodes import router_node, rewrite_node, retrieve_node, rerank_node
from evaluation.dataset import EVAL_QUESTIONS

logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger(__name__)

configure_settings()


def run_pipeline_for_eval(question: str) -> dict:
    """Runs retrieval (not generation) to collect contexts for scoring,
    plus a real generated answer using the same context."""
    state = {"question": question, "session_id": "eval-session"}
    state.update(router_node(state))
    state.update(rewrite_node(state))
    state.update(retrieve_node(state))
    state.update(rerank_node(state))

    contexts = [n.node.get_content() for n in state["reranked_nodes"]]
    context_str = "\n\n".join(contexts)

    prompt = (
        f"Answer the question using ONLY the context below. "
        f"If the context doesn't contain the answer, say so.\n\n"
        f"Context:\n{context_str}\n\nQuestion: {question}\nAnswer:"
    )
    answer = str(Settings.llm.complete(prompt))

    return {"contexts": contexts, "answer": answer}


def main():
    rows = []
    for item in EVAL_QUESTIONS:
        logger.info("Running pipeline for: %s", item["question"])
        result = run_pipeline_for_eval(item["question"])
        rows.append({
            "question": item["question"],
            "contexts": result["contexts"],
            "answer": result["answer"],
            "ground_truth": item["ground_truth"],
        })

    dataset = Dataset.from_list(rows)

    # RAGAS needs an LLM and embedding model to act as the "judge" --
    # we reuse our existing local Ollama setup rather than requiring
    # a separate OpenAI key just for evaluation.
    ragas_llm = LlamaIndexLLMWrapper(Settings.llm)
    ragas_embeddings = LlamaIndexEmbeddingsWrapper(Settings.embed_model)

    results = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=ragas_llm,
        embeddings=ragas_embeddings,
    )

    print("\n=== Evaluation Results ===")
    print(results)
    df = results.to_pandas()
    df.to_csv("evaluation_results.csv", index=False)
    print("\nSaved detailed results to evaluation_results.csv")


if __name__ == "__main__":
    main()
