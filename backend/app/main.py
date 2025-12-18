from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.api.api_v1.endpoints import search
from backend.app.core.config import settings
import os

app = FastAPI(title="Mufettis Agent API", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for Vercel/Production 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api/v1/search", tags=["search"])

# Serve PDFs (Mount data/raw directory)
pdf_directory = os.path.join(os.getcwd(), "data", "raw")
if os.path.isdir(pdf_directory):
    app.mount("/pdfs", StaticFiles(directory=pdf_directory), name="pdfs")
else:
    print(f"WARNING: PDF directory not found at {pdf_directory}")

@app.get("/")
def read_root():
    return {"message": "Mufettis Agent Backend is running", "details": "Use /docs for API documentation."}

@app.get("/version")
def check_version():
    return {"version": "LIVE_CHECK_v2", "conf": "GEMINI_2.5_FLASH_STD"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
