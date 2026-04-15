import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    UPLOAD_DIR = 'source'
    CHROMA_COLLECTION_NAME = "wiki_sections"
    SOURCE_DB_NAME = "database/source.db"
    WIKI_BASE_DIR = "wiki"
    INDEX_FILE_PATH = WIKI_BASE_DIR + "/index.md"
    LOG_FILE = "logs/ingestion.log"
