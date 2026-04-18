from langchain.tools import BaseTool

from core.config import Config


class IndexRead(BaseTool):
    name: str = "index_read"
    description: str = "Reads the wiki index file index.md."

    def _run(self):
        print(f"[TOOL] Reading index file")
        try:
            with open(Config.INDEX_FILE_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading index file: {e}"
