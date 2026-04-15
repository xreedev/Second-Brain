from langchain.tools import BaseTool
from core.config import Config
import os

class WikiRead(BaseTool):
    name: str = "wiki_read"
    description: str = "Reads the content of a wiki file"

    def _run(self, file_name: str):
        file_path = os.path.join(Config.WIKI_BASE_DIR, file_name)
        if not os.path.exists(file_path):
            return f"File does not exist: {file_path}"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return content
        except Exception as e:
            return f"Error reading file: {e}"
