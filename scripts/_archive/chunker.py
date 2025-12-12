import json
import re
from pathlib import Path
import uuid

def create_chunk(content, chunk_type, source, page, metadata=None):
    if metadata is None:
        metadata = {}
    
    return {
        "id": str(uuid.uuid4()),
        "content": content,
        "type": chunk_type,
        "source": source,
        "page": page,
        "metadata": metadata
    }

def process_text_blocks(text, source, page_num):
    """
    Split text into Articles (MADDE X) and Paragraphs.
    Injects context (filename) at the start of each chunk.
    """
    chunks = []
    lines = text.split('\n')
    
    current_chunk_lines = []
    current_type = "paragraph"
    current_meta = {}
    
    # Identify the specific document type for context
    # Clean filename for display (remove .pdf, etc)
    doc_name = source.replace(".pdf", "").replace("-", " ").replace("_", " ")
    context_header = f"BELGE: {doc_name}\n"
    
    # Regex for "MADDE <number>"
    article_pattern = re.compile(r'^\s*MADDE\s+(\d+)', re.IGNORECASE)
    
    for line in lines:
        match = article_pattern.match(line)
        if match:
            # If we have accumulated text, save it as previous chunk
            if current_chunk_lines:
                content = "\n".join(current_chunk_lines).strip()
                if content:
                    # Prepend context to the content
                    full_content = context_header + content
                    chunks.append(create_chunk(full_content, current_type, source, page_num, current_meta))
            
            # Start new article chunk
            current_chunk_lines = [line]
            current_type = "article"
            current_meta = {"article_number": match.group(1)}
        else:
            current_chunk_lines.append(line)
            
    # Flush last chunk
    if current_chunk_lines:
        content = "\n".join(current_chunk_lines).strip()
        if content:
             full_content = context_header + content
             chunks.append(create_chunk(full_content, current_type, source, page_num, current_meta))
            
    return chunks

def process_file(json_file, output_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    filename = data.get("filename", "unknown")
    all_file_chunks = []
    
    for page in data.get("pages", []):
        page_num = page.get("page_number")
        
        # 1. Process Tables
        tables = page.get("tables", [])
        for table in tables:
            # Filter None values
            cleaned_table = [[str(cell) if cell is not None else "" for cell in row] for row in table]
            table_str = "\n".join([" | ".join(row) for row in cleaned_table])
            
            # Add context to table
            doc_name = filename.replace(".pdf", "").replace("-", " ")
            full_table = f"BELGE: {doc_name} (TABLO)\n{table_str}"

            all_file_chunks.append(create_chunk(
                content=full_table,
                chunk_type="table",
                source=filename,
                page=page_num,
                metadata={"rows": len(table)}
            ))
            
        # 2. Process Text
        text = page.get("text", "")
        if text:
            # Extract text blocks
            text_chunks = process_text_blocks(text, filename, page_num)
            all_file_chunks.extend(text_chunks)
            
    # Write to JSONL (append mode)
    with open(output_file, 'a', encoding='utf-8') as f:
        for chunk in all_file_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

def main():
    processed_dir = Path("data/processed")
    chunks_dir = Path("data/chunks")
    chunks_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure output file is clean at the start of the script if running in batch?
    # Actually checking for file existence and deleting might be safer in the pipeline script,
    # but let's assume pipeline.bat handled the cleanup or we just append.
    # To be safe for this specific script run:
    output_file = chunks_dir / "all_chunks.jsonl"
    
    processed_files = list(processed_dir.glob("*.json"))
    print(f"Found {len(processed_files)} processed files.")
    
    for p_file in processed_files:
        print(f"Chunking {p_file.name}...")
        process_file(p_file, output_file)
    
    print("Chunking process complete.")

if __name__ == "__main__":
    main()
