"""
Docling Chunker - Improved Version
===================================
- Fixed encoding for Turkish characters
- Larger chunk size (768 tokens)
- Better context injection
- Clean JSONL output
"""

import json
import os
import logging
import codecs
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from docling.document_converter import DocumentConverter
    from docling.chunking import HybridChunker
    from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
    from transformers import AutoTokenizer
except ImportError:
    logger.error("Docling or Transformers not installed. Please run: poetry add docling transformers")
    exit(1)

# === CONFIG ===
EMBED_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MAX_TOKENS = 768  # Increased from 512 for better context


def fix_encoding(text: str) -> str:
    """
    Fix common encoding issues (mojibake) in text.
    Handles cases where UTF-8 text was incorrectly decoded as Latin-1.
    """
    if not text:
        return text
    
    try:
        # Try to fix double-encoded UTF-8 (common mojibake pattern)
        # This happens when UTF-8 bytes are interpreted as Latin-1 and then encoded to UTF-8 again
        fixed = text.encode('latin-1').decode('utf-8')
        return fixed
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    
    try:
        # Try CP1252 (Windows encoding)
        fixed = text.encode('cp1252').decode('utf-8')
        return fixed
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    
    # If no fix worked, return original
    return text


def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    if not text:
        return text
    
    # Fix encoding first
    text = fix_encoding(text)
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    # Remove control characters except newlines
    text = ''.join(c for c in text if c == '\n' or c.isprintable())
    
    return text.strip()


def main():
    raw_dir = Path("data/raw")
    md_out_dir = Path("data/md-chunks")
    chunks_out_file = Path("data/chunks/all_chunks.jsonl")
    
    # Ensure directories exist
    md_out_dir.mkdir(parents=True, exist_ok=True)
    chunks_out_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize Tokenizer & Chunker with larger token limit
    logger.info(f"Initializing Tokenizer ({EMBED_MODEL_ID}) with max_tokens={MAX_TOKENS}...")
    try:
        hf_tokenizer = HuggingFaceTokenizer(
            tokenizer=AutoTokenizer.from_pretrained(EMBED_MODEL_ID),
            max_tokens=MAX_TOKENS
        )
        chunker = HybridChunker(tokenizer=hf_tokenizer, merge_peers=True)
    except Exception as e:
        logger.error(f"Failed to initialize tokenizer/chunker: {e}")
        return

    converter = DocumentConverter()
    
    pdf_files = list(raw_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {raw_dir.absolute()}")
        return

    logger.info(f"Found {len(pdf_files)} PDFs. Starting processing...")
    
    # FRESH START: Remove old chunks file to avoid mixing old/new data
    if chunks_out_file.exists():
        logger.info("Removing old chunks file for fresh start...")
        chunks_out_file.unlink()
    
    total_chunks = 0
    
    for pdf_file in pdf_files:
        logger.info(f"Processing: {pdf_file.name}")
        file_chunks = []
        
        try:
            # 1. Convert PDF to structured document
            result = converter.convert(str(pdf_file))
            doc = result.document
            if not doc:
                logger.error(f"Conversion returned empty document for {pdf_file.name}")
                continue
            
            # 2. Chunk the document
            chunks = list(chunker.chunk(dl_doc=doc))
            logger.info(f"  > Generated {len(chunks)} chunks.")
            
            # 3. Save MD visual chunks (for debugging)
            md_filename = f"{pdf_file.stem}-chunk.md"
            md_path = md_out_dir / md_filename
            
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(f"# {pdf_file.name} - Extracted Chunks\n\n")
                for i, chunk in enumerate(chunks):
                    enriched_text = chunker.contextualize(chunk)
                    # Clean the text
                    cleaned_text = clean_text(enriched_text)
                    f.write(f"## === CHUNK {i} ===\n\n")
                    f.write(cleaned_text)
                    f.write("\n\n---\n\n")
            
            logger.info(f"  > Saved markdown to {md_path.name}")
            
            # 4. Prepare JSONL records with clean encoding
            for i, chunk in enumerate(chunks):
                enriched_text = chunker.contextualize(chunk)
                # Clean and fix encoding
                cleaned_content = clean_text(enriched_text)
                
                # Skip empty chunks
                if not cleaned_content or len(cleaned_content.strip()) < 10:
                    continue
                
                # Extract page numbers
                pages = set()
                if hasattr(chunk, 'meta') and hasattr(chunk.meta, 'doc_items'):
                    for item in chunk.meta.doc_items:
                        if hasattr(item, 'prov') and item.prov:
                            for p in item.prov:
                                if hasattr(p, 'page_no'):
                                    pages.add(p.page_no)
                
                page_list = sorted(list(pages))
                primary_page = page_list[0] if page_list else 1
                
                chunk_record = {
                    "id": f"{pdf_file.stem}_{i}",
                    "content": cleaned_content,
                    "source": pdf_file.name,
                    "page": primary_page,
                    "type": "text",  # Default type
                    "metadata": {
                        "source": pdf_file.name,
                        "pages": page_list,
                        "chunk_index": i,
                        "char_count": len(cleaned_content)
                    }
                }
                file_chunks.append(chunk_record)
            
            # 5. Append to Master JSONL with proper encoding
            with open(chunks_out_file, "a", encoding="utf-8") as f:
                for record in file_chunks:
                    # Ensure proper JSON encoding with Turkish characters
                    json_line = json.dumps(record, ensure_ascii=False)
                    f.write(json_line + "\n")
            
            total_chunks += len(file_chunks)
            logger.info(f"  > Appended {len(file_chunks)} chunks to {chunks_out_file.name}")
                
        except Exception as e:
            logger.error(f"Failed to process {pdf_file.name}: {e}", exc_info=True)
    
    logger.info(f"\n{'='*50}")
    logger.info(f"DONE! Total chunks created: {total_chunks}")
    logger.info(f"Chunks saved to: {chunks_out_file}")
    logger.info(f"{'='*50}")
    logger.info("\nNext step: Run 'poetry run python scripts/embed_and_index.py' to build the vector index.")


if __name__ == "__main__":
    main()
