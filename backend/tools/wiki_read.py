from typing import List
from langchain.tools import BaseTool
from pydantic import BaseModel
from core.config import Config
import os


class WikiReadInput(BaseModel):
    files: List[str]


class WikiRead(BaseTool):
    name: str = "wiki_read"
    description: str = "Reads the content of a wiki file. Takes a list of filenames."
    args_schema: type[BaseModel] = WikiReadInput

    def _run(self, files: List[str]) -> List[str]:
        print(f"[TOOL] Reading wiki files - {len(files)} file(s)")
        contents = []
        for file_name in files:
            file_path = os.path.join(Config.WIKI_BASE_DIR, file_name)
            if not os.path.exists(file_path):
                contents.append(f"File does not exist: {file_path}")
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                contents.append(content)
            except Exception as e:
                contents.append(f"Error reading file: {e}")
        return contents
