import json

TARGET_FILE = "6098-Borçlar Kanunu.pdf"
TARGET_TERM = "Madde 8" # Case insensitive search

print(f"Searching for '{TARGET_TERM}' in {TARGET_FILE}...")
found_file = False
match_count = 0

with open("data/chunks/all_chunks.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)
        if data.get("source") == TARGET_FILE:
            found_file = True
            content = data.get("content", "")
            
            # Normalize for search
            if TARGET_TERM.lower() in content.lower():
                print(f"--- FOUND MATCH in Chunk {data['id']} ---")
                print(content[:500]) # Print first 500 chars
                print("------------------------------------------")
                match_count += 1
            
            # Check for alternative "MADDE 8"
            if "MADDE 8" in content:
                print(f"--- FOUND EXACT 'MADDE 8' in Chunk {data['id']} ---")
                
if not found_file:
    print(f"ERROR: No chunks found for source: {TARGET_FILE}")
else:
    print(f"Finished. Found {match_count} matches for '{TARGET_TERM}' inside the file.")
