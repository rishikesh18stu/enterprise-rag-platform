"""
Hand-written evaluation set: questions with known-correct ground truth
answers, based on content we know is in the knowledge base. Small and
manually curated is fine -- RAGAS doesn't need thousands of examples
to give useful signal for a project like this.
"""

EVAL_QUESTIONS = [
    {
        "question": "What is retrieval-augmented generation?",
        "ground_truth": (
            "Retrieval-augmented generation (RAG) is a technique that enables "
            "large language models to retrieve and incorporate information from "
            "external data sources to generate more accurate, up-to-date responses."
        ),
    },
    {
        "question": "Why do penguins live in colonies?",
        "ground_truth": (
            "Penguins live in colonies for protection from predators, to share "
            "responsibilities like incubating eggs and feeding chicks, and to "
            "improve survival chances through mutual support."
        ),
    },
    {
        "question": "What is the candidate's GitHub username?",
        "ground_truth": "github.com/rishikesh18stu",
    },
]
