import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Mufettis Agent"
    API_V1_STR: str = "/api/v1"
    
    # Security
    # SECRET_KEY: str = "..." 
    
    # External APIs
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Vector DB
    CHROMA_DB_PATH: str = "data/chroma_db"
    CHROMA_COLLECTION_NAME: str = "bank_mevzuat"

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
    }

settings = Settings()
