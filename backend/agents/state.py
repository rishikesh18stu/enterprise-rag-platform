from typing import TypedDict, Optional


class RAGState(TypedDict):
    """
    Shared state passed between every node in the graph.
    Each node reads what it needs and adds/updates fields --
    LangGraph merges these updates automatically as the graph runs.
    """
    question: str 
    route: Optional[str]                   # original user question, never overwritten
    rewritten_question: Optional[str]   # output of the rewrite node
    retrieved_nodes: Optional[list]     # chunks after retrieval + merge
    reranked_nodes: Optional[list]      # chunks after reranking
    answer: Optional[str]               # final generated answer
    citations: Optional[list]
    session_id: str