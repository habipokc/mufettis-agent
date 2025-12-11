import chromadb
from pathlib import Path

db_path = Path("data/chroma_db")
client = chromadb.PersistentClient(path=str(db_path))
try:
    collection = client.get_collection(name="bank_mevzuat")
    count = collection.count()
    print(f"Collection 'bank_mevzuat' has {count} documents.")
    if count > 0:
        print("First document preview:", collection.peek(limit=1))
except Exception as e:
    print(f"Error accessing collection: {e}")
