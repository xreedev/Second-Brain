import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    VERCEL_API_KEY = os.getenv("VERCEL_API_KEY")
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
    UPLOAD_DIR = 'source'
    CHROMA_COLLECTION_NAME = "wiki_sections"
    SOURCE_DB_NAME = "database/source.db"
    WIKI_BASE_DIR = "wiki"
    INDEX_FILE_PATH = WIKI_BASE_DIR + "/index.md"
    INDEX_MAP_FILE_PATH = WIKI_BASE_DIR + "/index.json"
    LOG_FILE = "logs/ingestion.log"
    CHAT_LOG_FILE = "logs/chat.log"
    CHAT_TOOL_LOG_FILE = "logs/chat_tools.log"
