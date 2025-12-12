import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GEMINI_API_KEY")
print(f"Key loaded: {key[:5]}...{key[-5:] if key else 'None'}")

if not key:
    print("Key is missing in .env")
    exit(1)

genai.configure(api_key=key)

try:
    result = genai.embed_content(
        model="models/embedding-001",
        content="Hello world",
        task_type="retrieval_query"
    )
    print("Embedding success!")
    print(result['embedding'][:5])
except Exception as e:
    print(f"Error: {e}")
