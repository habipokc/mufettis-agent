import chromadb
from pathlib import Path

db_path = Path("data/chroma_db")
client = chromadb.PersistentClient(path=str(db_path))
collection = client.get_collection(name="bank_mevzuat")

# Query for TCK chunks
target_file = "5237-Türk Ceza Kanunu.pdf"
results = collection.get(
    where={"source": target_file},
    limit=5
)

count = len(results['ids'])
print(f"Found {count} chunks for '{target_file}'")

if count == 0:
    print("CRITICAL: TCK is missing from index!")
else:
    print("TCK exists. First chunk preview:")
    print(results['documents'][0][:200] if results['documents'] else "No text")
    
# Also check total files indexed
all_data = collection.get(include=['metadatas'])
unique_sources = set(m['source'] for m in all_data['metadatas'])
print(f"\nTotal unique files indexed: {len(unique_sources)}")
if target_file not in unique_sources:
    print(f"Confirming: {target_file} is NOT in the unique sources list.")
else:
    print(f"Confirming: {target_file} IS in the list.")
