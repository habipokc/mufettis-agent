import chromadb
from google import genai
from typing import List, Dict, Any
from backend.app.core.config import settings

# Initialize Chroma Client
try:
    chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
    collection = chroma_client.get_or_create_collection(name=settings.CHROMA_COLLECTION_NAME)
except Exception as e:
    print(f"Chroma DB Connection Error: {e}")
    collection = None

# Initialize Gemini Client
# Client gets API key from GEMINI_API_KEY env var automatically, 
# or we can pass it explicitly if needed (api_key=settings.GEMINI_API_KEY)
client = None
if settings.GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
    except Exception as e:
        print(f"Gemini Client Init Error: {e}")

def get_embedding(text: str) -> List[float]:
    if not client:
        raise Exception("Gemini Client not initialized (Missing Key?)")
    try:
        # New SDK Embedding call
        result = client.models.embed_content(
            model="text-embedding-004", # or 'models/text-embedding-004' or 'embedding-001'
            contents=text,
            config=None # task_type might be in config if needed
        )
        # Result structure might differ. Previously result['embedding']. 
        # In new SDK, check attributes. commonly result.embeddings[0].values
        # Let's assume result.embeddings[0].values based on new SDK docs usually.
        # Check if result is an object or dict. 
        # The user provided template for generate, not embed. 
        # But commonly: result.embeddings[0].values
        if hasattr(result, 'embeddings') and result.embeddings:
             return result.embeddings[0].values
        return []
    except Exception as e:
        print(f"Embedding error: {e}")
        raise e

def query_rag(query_text: str, n_results: int = 15) -> Dict[str, Any]:
    if not collection:
        return {"error": "Vector DB not initialized"}

    # 1. Embed Query
    try:
        query_emb = get_embedding(query_text)
    except Exception as e:
        return {"error": str(e)}

    if not query_emb:
        return {"error": "Failed to generate embedding"}

    # 2. Retrieve from Chroma
    print("Retrieving from Chroma...")
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    print(f"Retrieved {len(results['documents'][0])} docs.")
    
    retrieved_docs = results['documents'][0]
    retrieved_metas = results['metadatas'][0]
    
    context_parts = []
    sources = []
    
    for i, doc in enumerate(retrieved_docs):
        meta = retrieved_metas[i]
        source_label = f"[{i+1}] Source: {meta.get('source', 'unknown')} (Page {meta.get('page', '?')})"
        context_parts.append(f"{source_label}\n{doc}")
        sources.append(meta)
        
    full_context = "\n\n".join(context_parts)
    
    # 3. Generate Answer
    prompt = f"""
    You are an expert banking auditor assistant (Müfettiş Yardımcısı).
    Use the following context snippets from Turkish banking regulations to answer the question.
    
    Context:
    {full_context}
    
    Question: {query_text}
    
    Instructions:
    - Answer in Turkish.
    - Cite sources using the numbers [1], [2] etc.
    - If the context doesn't contain the answer, say "Mevzuatta bu konuda bilgi bulamadım."
    - Be professional and precise.
    """
    
    try:
        # Gemini ile yanıt üret
        print("Calling Gemini Generation...")
        model_name = "gemini-2.5-flash"
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        print("Gemini response received.")
        answer = response.text
    except Exception as e:
        print(f"Generation Error: {e}")
        answer = f"Error generating answer: {e}"
        
    return {
        "answer": answer,
        "sources": sources,
        "context_used": full_context
    }
