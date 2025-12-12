import requests
import json

API_URL = "http://localhost:8000/api/v1/search/"

def test_query(query, description):
    print(f"\n--- TEST: {description} ---")
    try:
        res = requests.post(API_URL, json={"query": query})
        res.raise_for_status()
        data = res.json()
        
        print(f"Query: {query}")
        print(f"Answer: {data['answer'][:100]}...") # Print first 100 chars
        print(f"Sources: {len(data['sources'])}")
        
        if len(data['sources']) > 0:
            print("  [OK] Sources returned (Expected for RAG)")
        else:
            print("  [OK] No sources (Expected for Chitchat)")
            
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_query("Merhaba", "Chitchat Routing")
    test_query("Kredi risklerine ilişkin yönetmelik nedir?", "RAG Routing")
