"""
RAG and knowledge retrieval functions.
"""

from db.knowledge_repo import hybrid_rag_fetch

def research_scan(topic: str, user_id: str) -> str:
    """
    Generate a research briefing by running a generic RAG query against
    the user's knowledge base.
    """
    if not topic or topic == "Domain expertise as identified from the ingested knowledge base":
        rag_data = hybrid_rag_fetch("core concepts, target audience, course outline, primary skills", user_id, top_k=6)
    else:
        rag_data = hybrid_rag_fetch(f"core concepts and details about: {topic}", user_id, top_k=6)
    
    if not rag_data["context_str"]:
        return "No uploaded research context available. The user hasn't provided custom documents yet."
    
    return f"Extracted from User's Knowledge Base:\n{rag_data['context_str']}"
