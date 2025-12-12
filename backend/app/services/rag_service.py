"""
RAG Service - Hybrid Retrieval + Reranking
==========================================
- Dense retrieval (MiniLM embeddings)
- Sparse retrieval (BM25)
- Cross-encoder reranking
- Optimized context window
"""

import chromadb
import json
from google import genai
from typing import List, Dict, Any, Tuple
from pathlib import Path
from backend.app.core.config import settings

# === Initialize Chroma Client ===
print("Initializing ChromaDB...")
try:
    chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
    collection = chroma_client.get_or_create_collection(name=settings.CHROMA_COLLECTION_NAME)
    print(f"ChromaDB initialized. Collection has {collection.count()} documents.")
except Exception as e:
    print(f"Chroma DB Connection Error: {e}")
    collection = None

# === Initialize Embedding Model (MiniLM) ===
print("Loading MiniLM embedding model...")
from sentence_transformers import SentenceTransformer, CrossEncoder

try:
    embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    print("✓ MiniLM Embedding Model loaded.")
except Exception as e:
    print(f"Embedding Model Load Error: {e}")
    embed_model = None

# === Initialize Cross-Encoder for Reranking ===
print("Loading Cross-Encoder reranking model...")
try:
    reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    print("✓ Cross-Encoder Reranker loaded.")
except Exception as e:
    print(f"Reranker Load Error: {e}")
    reranker = None

# === Initialize BM25 Index ===
print("Building BM25 index...")
from rank_bm25 import BM25Okapi
import re

bm25_index = None
bm25_documents = []
bm25_ids = []
bm25_metadatas = []

def tokenize_turkish(text: str) -> List[str]:
    """Simple Turkish-aware tokenizer."""
    # Lowercase and split on non-alphanumeric
    text = text.lower()
    # Keep Turkish characters
    tokens = re.findall(r'[a-zçğıöşü0-9]+', text)
    # Remove very short tokens
    return [t for t in tokens if len(t) > 2]

def build_bm25_index():
    """Build BM25 index from all documents in ChromaDB."""
    global bm25_index, bm25_documents, bm25_ids, bm25_metadatas
    
    if not collection:
        print("Cannot build BM25 index: ChromaDB not available")
        return
    
    try:
        # Get all documents from ChromaDB
        all_data = collection.get(include=["documents", "metadatas"])
        
        if not all_data["documents"]:
            print("No documents found in ChromaDB")
            return
        
        bm25_documents = all_data["documents"]
        bm25_ids = all_data["ids"]
        bm25_metadatas = all_data["metadatas"] if all_data["metadatas"] else [{}] * len(bm25_documents)
        
        # Tokenize all documents
        tokenized_docs = [tokenize_turkish(doc) for doc in bm25_documents]
        
        # Build BM25 index
        bm25_index = BM25Okapi(tokenized_docs)
        print(f"✓ BM25 index built with {len(bm25_documents)} documents.")
        
    except Exception as e:
        print(f"BM25 Index Build Error: {e}")

# Build BM25 index on startup
build_bm25_index()

# === Initialize Gemini Client (for Generation) ===
print("Initializing Gemini client...")
gemini_client = None
if settings.GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        print("✓ Gemini client initialized.")
    except Exception as e:
        print(f"Gemini Client Init Error: {e}")
else:
    print("⚠ GEMINI_API_KEY not set")


def get_embedding(text: str) -> List[float]:
    """Generate embedding using local MiniLM model."""
    if not embed_model:
        raise Exception("Embedding model not initialized.")
    try:
        return embed_model.encode(text).tolist()
    except Exception as e:
        print(f"Embedding error: {e}")
        raise e


def hybrid_retrieve(query: str, n_dense: int = 20, n_sparse: int = 20) -> List[Tuple[str, Dict, str, float]]:
    """
    Hybrid retrieval: Dense (embedding) + Sparse (BM25)
    
    Returns: List of (document, metadata, doc_id, score) tuples
    """
    results = {}  # doc_id -> (doc, meta, combined_score)
    
    # 1. Dense Retrieval (ChromaDB)
    if collection and embed_model:
        try:
            query_emb = get_embedding(query)
            dense_results = collection.query(
                query_embeddings=[query_emb],
                n_results=n_dense,
                include=["documents", "metadatas", "distances"]
            )
            
            for i, doc_id in enumerate(dense_results["ids"][0]):
                doc = dense_results["documents"][0][i]
                meta = dense_results["metadatas"][0][i] if dense_results["metadatas"] else {}
                distance = dense_results["distances"][0][i] if dense_results["distances"] else 1.0
                
                # Convert distance to similarity score (ChromaDB uses L2 distance)
                # Lower distance = more similar
                dense_score = 1 / (1 + distance)
                
                if doc_id not in results:
                    results[doc_id] = {"doc": doc, "meta": meta, "dense_score": dense_score, "bm25_score": 0}
                else:
                    results[doc_id]["dense_score"] = dense_score
                    
        except Exception as e:
            print(f"Dense retrieval error: {e}")
    
    # 2. Sparse Retrieval (BM25)
    if bm25_index and bm25_documents:
        try:
            tokenized_query = tokenize_turkish(query)
            bm25_scores = bm25_index.get_scores(tokenized_query)
            
            # Get top N indices
            top_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:n_sparse]
            
            # Normalize BM25 scores
            max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1
            
            for idx in top_indices:
                if bm25_scores[idx] > 0:  # Only include if there's some match
                    doc_id = bm25_ids[idx]
                    doc = bm25_documents[idx]
                    meta = bm25_metadatas[idx] if idx < len(bm25_metadatas) else {}
                    normalized_score = bm25_scores[idx] / max_bm25
                    
                    if doc_id not in results:
                        results[doc_id] = {"doc": doc, "meta": meta, "dense_score": 0, "bm25_score": normalized_score}
                    else:
                        results[doc_id]["bm25_score"] = normalized_score
                        
        except Exception as e:
            print(f"BM25 retrieval error: {e}")
    
    # 3. Combine scores (weighted average)
    # Dense weight: 0.6, BM25 weight: 0.4
    combined = []
    for doc_id, data in results.items():
        combined_score = 0.6 * data["dense_score"] + 0.4 * data["bm25_score"]
        combined.append((data["doc"], data["meta"], doc_id, combined_score))
    
    # Sort by combined score
    combined.sort(key=lambda x: x[3], reverse=True)
    
    return combined


def rerank_results(query: str, candidates: List[Tuple[str, Dict, str, float]], top_k: int = 5) -> List[Tuple[str, Dict, str, float]]:
    """
    Rerank candidates using Cross-Encoder.
    
    Args:
        query: User query
        candidates: List of (document, metadata, doc_id, initial_score) tuples
        top_k: Number of results to return
    
    Returns:
        Reranked list of (document, metadata, doc_id, rerank_score) tuples
    """
    if not reranker or not candidates:
        return candidates[:top_k]
    
    try:
        # Prepare pairs for cross-encoder
        documents = [c[0] for c in candidates]
        pairs = [[query, doc] for doc in documents]
        
        # Get reranking scores
        rerank_scores = reranker.predict(pairs)
        
        # Combine with original data
        reranked = []
        for i, (doc, meta, doc_id, _) in enumerate(candidates):
            reranked.append((doc, meta, doc_id, float(rerank_scores[i])))
        
        # Sort by rerank score
        reranked.sort(key=lambda x: x[3], reverse=True)
        
        return reranked[:top_k]
        
    except Exception as e:
        print(f"Reranking error: {e}")
        return candidates[:top_k]


def query_rag(query_text: str, n_results: int = 5) -> Dict[str, Any]:
    """
    Main RAG query function with hybrid retrieval and reranking.
    
    Args:
        query_text: User's question
        n_results: Number of final results to use in context (default: 5)
    
    Returns:
        Dict with answer, sources, and context
    """
    if not collection:
        return {"error": "Vector DB not initialized"}
    
    print(f"\n{'='*50}")
    print(f"Query: {query_text}")
    print(f"{'='*50}")
    
    # 1. Hybrid Retrieval (Dense + BM25)
    print("Step 1: Hybrid retrieval...")
    candidates = hybrid_retrieve(query_text, n_dense=30, n_sparse=30)
    print(f"  Retrieved {len(candidates)} unique candidates")
    
    if not candidates:
        return {"error": "No relevant documents found", "answer": "Üzgünüm, bu konuda mevzuatta ilgili bir bilgi bulamadım.", "sources": []}
    
    # 2. Reranking (Cross-Encoder)
    print("Step 2: Reranking with Cross-Encoder...")
    top_results = rerank_results(query_text, candidates, top_k=n_results)
    print(f"  Top {len(top_results)} results after reranking")
    
    # 3. Build Context
    print("Step 3: Building context...")
    context_parts = []
    sources = []
    
    for i, (doc, meta, doc_id, score) in enumerate(top_results):
        source_name = meta.get('source', 'Bilinmeyen Kaynak')
        page = meta.get('page', '?')
        
        # Clean source name for display
        source_display = source_name.replace('.pdf', '')
        
        source_label = f"[{i+1}] {source_display} (Sayfa {page})"
        context_parts.append(f"{source_label}\n{doc}")
        
        sources.append({
            "source": source_name,
            "page": page,
            "score": round(score, 4),
            "chunk_id": doc_id
        })
    
    full_context = "\n\n---\n\n".join(context_parts)
    print(f"  Context built with {len(context_parts)} chunks")
    
    # 4. Generate Answer with Gemini
    print("Step 4: Generating answer with Gemini...")
    
    prompt = f"""Sen bir Türk bankacılık mevzuatı uzmanısın (Müfettiş Yardımcısı).
Aşağıdaki mevzuat bölümlerini kullanarak soruyu yanıtla.

### MEVZUAT BÖLÜMLERİ:
{full_context}

### SORU:
{query_text}

### TALİMATLAR:
1. Yanıtını Türkçe ver.
2. Sadece verilen mevzuat bölümlerindeki bilgileri kullan.
3. Kaynak numaralarını kullan: [1], [2], vb.
4. Eğer bilgi bulamazsan "Bu konuda mevzuatta açık bir bilgi bulamadım" de.
5. Profesyonel ve net ol.
6. Yanıtın sonunda kullandığın kaynakları listele.

### YANITINIZ:"""

    try:
        if not gemini_client:
            raise Exception("Gemini client not initialized")
            
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        answer = response.text
        print("  ✓ Answer generated successfully")
        
    except Exception as e:
        print(f"  ✗ Generation Error: {e}")
        answer = f"Yanıt üretilirken bir hata oluştu: {e}"
    
    return {
        "answer": answer,
        "sources": sources,
        "context_used": full_context,
        "retrieval_stats": {
            "candidates_retrieved": len(candidates),
            "results_after_rerank": len(top_results)
        }
    }
