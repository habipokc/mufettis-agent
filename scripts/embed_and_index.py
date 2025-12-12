"""
Embed and Index - Improved Version
====================================
- Uses local SentenceTransformer (MiniLM)
- Clean collection reset
- Progress tracking
- Batch processing with error handling
"""

import json
import os
import chromadb
from pathlib import Path
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# === Config ===
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "bank_mevzuat"
BATCH_SIZE = 100  # Increased for efficiency

# Initialize embedding model
logger.info(f"Loading embedding model: {EMBED_MODEL_NAME}...")
model = SentenceTransformer(EMBED_MODEL_NAME)
logger.info("✓ Embedding model loaded.")


def get_embedding(text: str) -> list | None:
    """Generate embedding using local SentenceTransformer model."""
    try:
        if not text or not text.strip():
            return None
        
        # Truncate very long texts to avoid memory issues
        max_chars = 8000  # ~2000 tokens roughly
        if len(text) > max_chars:
            text = text[:max_chars]
        
        embedding = model.encode(text).tolist()
        return embedding
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        return None


def main():
    """Main function - embed chunks and index to ChromaDB."""
    chunks_file = Path("data/chunks/all_chunks.jsonl")
    if not chunks_file.exists():
        logger.error(f"No chunks found at {chunks_file}")
        logger.info("Please run 'poetry run python scripts/docling_chunker.py' first.")
        return

    # Initialize Chroma
    db_path = Path("data/chroma_db")
    db_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Initializing ChromaDB at {db_path}...")
    chroma_client = chromadb.PersistentClient(path=str(db_path))
    
    # RESET: Delete old collection to ensure clean state
    # This prevents dimension mismatch errors (768 vs 384)
    try:
        chroma_client.delete_collection(name=COLLECTION_NAME)
        logger.info("Deleted existing collection for clean rebuild.")
    except Exception:
        pass  # Collection might not exist
    
    collection = chroma_client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}  # Use cosine similarity
    )
    logger.info(f"Created fresh collection: {COLLECTION_NAME}")
    
    # Count total chunks
    total_chunks = sum(1 for _ in open(chunks_file, 'r', encoding='utf-8'))
    logger.info(f"Found {total_chunks} chunks to process.")
    
    # Process in batches
    batch_docs = []
    batch_ids = []
    batch_metas = []
    batch_embs = []
    
    processed = 0
    skipped = 0
    
    with open(chunks_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                chunk = json.loads(line)
                
                content = chunk.get("content", "")
                chunk_id = chunk.get("id", f"chunk_{line_num}")
                
                # Skip empty content
                if not content or len(content.strip()) < 10:
                    skipped += 1
                    continue
                
                # Prepare metadata
                meta = chunk.get("metadata", {})
                meta["source"] = chunk.get("source", "unknown")
                meta["page"] = chunk.get("page", 0)
                meta["type"] = chunk.get("type", "text")
                
                # Ensure all metadata values are primitives (ChromaDB requirement)
                clean_meta = {}
                for k, v in meta.items():
                    if isinstance(v, (str, int, float, bool)):
                        clean_meta[k] = v
                    elif isinstance(v, list):
                        clean_meta[k] = str(v)  # Convert lists to string
                    else:
                        clean_meta[k] = str(v)
                
                # Generate embedding
                emb = get_embedding(content)
                if emb is None:
                    skipped += 1
                    continue
                
                batch_docs.append(content)
                batch_ids.append(chunk_id)
                batch_metas.append(clean_meta)
                batch_embs.append(emb)
                
                # Process batch when full
                if len(batch_docs) >= BATCH_SIZE:
                    _upsert_batch(collection, batch_docs, batch_ids, batch_metas, batch_embs)
                    processed += len(batch_docs)
                    logger.info(f"Progress: {processed}/{total_chunks} chunks indexed ({processed*100//total_chunks}%)")
                    
                    # Reset batch
                    batch_docs = []
                    batch_ids = []
                    batch_metas = []
                    batch_embs = []
                    
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON at line {line_num}: {e}")
                skipped += 1
            except Exception as e:
                logger.warning(f"Error processing line {line_num}: {e}")
                skipped += 1
    
    # Process final batch
    if batch_docs:
        _upsert_batch(collection, batch_docs, batch_ids, batch_metas, batch_embs)
        processed += len(batch_docs)
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info(f"INDEXING COMPLETE!")
    logger.info(f"{'='*50}")
    logger.info(f"Total processed: {processed}")
    logger.info(f"Skipped: {skipped}")
    logger.info(f"Collection size: {collection.count()}")
    logger.info(f"\nRestart the backend server to use the new index.")


def _upsert_batch(collection, documents: list, ids: list, metadatas: list, embeddings: list):
    """Upsert a batch of documents to ChromaDB."""
    try:
        collection.upsert(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
    except Exception as e:
        logger.error(f"Batch upsert error: {e}")
        # Try one by one as fallback
        for i in range(len(documents)):
            try:
                collection.upsert(
                    documents=[documents[i]],
                    embeddings=[embeddings[i]],
                    metadatas=[metadatas[i]],
                    ids=[ids[i]]
                )
            except Exception as e2:
                logger.error(f"Failed to upsert chunk {ids[i]}: {e2}")


if __name__ == "__main__":
    main()
