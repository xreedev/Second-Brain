import os
import re
from typing import List
from langchain.tools import BaseTool
from pydantic import BaseModel, PrivateAttr
from files_service import IndexMapService
from database.sqllite_service import SQLiteService
from core.config import Config


class WikiSectionReadItem(BaseModel):
    section_id: str


class WikiSectionReadInput(BaseModel):
    requests: List[WikiSectionReadItem]


class WikiSectionRead(BaseTool):
    name: str = "wiki_section_read"
    description: str = (
        "Read wiki sections by section_id. "
        "Returns section content."
    )

    args_schema: type[BaseModel] = WikiSectionReadInput

    _message_id: str = PrivateAttr()
    _index_service: object = PrivateAttr()

    def __init__(self, message_id: str, **kwargs):
        super().__init__(**kwargs)
        self._message_id = message_id
        self._index_service = IndexMapService()

    def _run(self, requests: List[WikiSectionReadItem]):
        print(f"[TOOL] Reading {len(requests)} section(s) for message_id={self._message_id}")

        if not os.path.exists(Config.INDEX_FILE_PATH):
            return [{"found": False, "error": "Index file missing"}]

        db = SQLiteService()
        results = []

        try:
            for request in requests:
                section_id = str(request.section_id)

                db.add_message_section(self._message_id, section_id)

                section_content = self._extract_section(section_id)

                if section_content is None:
                    results.append({
                        "section_id": section_id,
                        "found": False,
                        "error": "Section not found",
                    })
                    continue

                results.append({
                    "section_id": section_id,
                    "found": True,
                    "content": section_content,
                })
        finally:
            db.close()

        return results

    def _extract_section(self, section_id: str):
        entry = self._index_service.get_entry(str(section_id))
        if not entry:
            return None

        file_name = entry.get("file_name")
        if not file_name:
            return None

        file_path = os.path.join(Config.WIKI_BASE_DIR, file_name)

        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return None

        anchor = f"<!-- section-id: {section_id} -->"

        if anchor not in content:
            return None

        pattern = r"(<!-- section-id: .+? -->)"
        parts = re.split(pattern, content)

        try:
            anchor_idx = parts.index(anchor)
        except ValueError:
            return None

        if anchor_idx + 1 >= len(parts):
            return None

        return parts[anchor_idx + 1].strip()
