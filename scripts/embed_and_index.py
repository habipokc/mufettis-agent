import json
import os
import chromadb
from google import genai
from chromadb.config import Settings
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai_client = None  # Değişken adı düzeltildi - chromadb client ile çakışmayı önlemek için

if GEMINI_API_KEY:
    try:
        genai_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Gemini Client Init Error: {e}")
else:
    print("WARNING: GEMINI_API_KEY not found. Embeddings will fail.")


def get_embedding(text: str) -> list | None:
    """Gemini API kullanarak metin embedding'i oluşturur."""
    try:
        if not text or not text.strip():
            return None
        
        if not genai_client:
            print("ERROR: Gemini client not initialized")
            return None
            
        result = genai_client.models.embed_content(
            model="text-embedding-004",
            contents=text
        )
        if hasattr(result, 'embeddings') and result.embeddings:
            return result.embeddings[0].values
        return None
    except Exception as e:
        print(f"Embedding error: {e}")
        return None


def main():
    """Ana fonksiyon - chunk'ları embedding'e dönüştürüp ChromaDB'ye yükler."""
    chunks_file = Path("data/chunks/all_chunks.jsonl")
    if not chunks_file.exists():
        print(f"No chunks found at {chunks_file}")
        return

    # Initialize Chroma
    db_path = Path("data/chroma_db")
    db_path.mkdir(parents=True, exist_ok=True)
    
    chroma_client = chromadb.PersistentClient(path=str(db_path))  # Ayrı değişken adı
    collection = chroma_client.get_or_create_collection(name="bank_mevzuat")
    
    print("Loading chunks...")
    batch_size = 50
    documents = []
    ids = []
    metadatas = []
    
    with open(chunks_file, 'r', encoding='utf-8') as f:
        for line in f:
            chunk = json.loads(line)
            
            # Prepare metadata
            meta = chunk.get("metadata", {})
            meta["source"] = chunk.get("source", "unknown")
            meta["page"] = chunk.get("page", 0)
            meta["type"] = chunk.get("type", "unknown")
            
            # Ensure metadata values are primitives for Chroma
            for k, v in meta.items():
                if not isinstance(v, (str, int, float, bool)):
                    meta[k] = str(v)
            
            documents.append(chunk["content"])
            ids.append(chunk["id"])
            metadatas.append(meta)
            
            if len(documents) >= batch_size:
                _process_batch(collection, documents, ids, metadatas)
                documents = []
                ids = []
                metadatas = []

    # Final batch
    if documents:
        _process_batch(collection, documents, ids, metadatas)
    
    print("Indexing complete.")


def _process_batch(collection, documents: list, ids: list, metadatas: list):
    """Bir batch'i embedding'e dönüştürüp ChromaDB'ye yükler."""
    if not GEMINI_API_KEY:
        print("WARNING: Skipping batch - no API key")
        return
        
    print(f"Embedding batch of {len(documents)}...")
    embeddings = [get_embedding(doc) for doc in documents]
    
    # Filter out failures
    batch_docs = []
    batch_ids = []
    batch_metas = []
    batch_embs = []
    
    for i, emb in enumerate(embeddings):
        if emb is not None:
            batch_docs.append(documents[i])
            batch_ids.append(ids[i])
            batch_metas.append(metadatas[i])
            batch_embs.append(emb)
    
    if batch_docs:
        collection.upsert(
            documents=batch_docs,
            embeddings=batch_embs,
            metadatas=batch_metas,
            ids=batch_ids
        )
        print(f"Upserted {len(batch_docs)} chunks.")


if __name__ == "__main__":
    main()
