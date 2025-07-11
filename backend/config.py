import os
from typing import List
from dotenv import load_dotenv
import logging

# Configure logging for config loading
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Debug: Check if .env file exists
env_file_path = os.path.join(os.getcwd(), '.env')
logger.info(f"Looking for .env file at: {env_file_path}")
logger.info(f".env file exists: {os.path.exists(env_file_path)}")

class Settings:
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # LangSmith Configuration
    LANGCHAIN_TRACING_V2: bool = os.getenv("LANGCHAIN_TRACING_V2", "true").lower() == "true"
    LANGCHAIN_ENDPOINT: str = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "autofill-form-app")
    
    # Pinecone Configuration
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "autofill-documents")
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # App Configuration
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000,https://localhost:3000").split(",")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB default
    
    # Model Configuration
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    CHAT_MODEL: str = "gpt-4-turbo"
    TEMPERATURE: float = 0.1
    MAX_TOKENS: int = 800
    
    # Vector Search Configuration
    TOP_K: int = 10
    SIMILARITY_THRESHOLD: float = 0.5
    
    # Chunking Configuration
    CHUNK_SIZE: int = 400
    CHUNK_OVERLAP: int = 100

settings = Settings()

# Debug logging for critical environment variables
logger.info("=== Environment Variables Debug ===")
logger.info(f"SUPABASE_URL set: {bool(settings.SUPABASE_URL)}")
logger.info(f"SUPABASE_ANON_KEY set: {bool(settings.SUPABASE_ANON_KEY)}")
logger.info(f"SUPABASE_SERVICE_ROLE_KEY set: {bool(settings.SUPABASE_SERVICE_ROLE_KEY)}")
logger.info(f"OPENAI_API_KEY set: {bool(settings.OPENAI_API_KEY)}")
logger.info(f"PINECONE_API_KEY set: {bool(settings.PINECONE_API_KEY)}")
logger.info("=== End Environment Variables Debug ===") 