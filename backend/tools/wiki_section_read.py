import os
import re
from typing import List
from langchain.tools import BaseTool
from pydantic import BaseModel, PrivateAttr

from core.config import Config
from files_service import IndexMapService


class WikiSectionReadItem(BaseModel):
    file_name: str
    section_id: str


class WikiSectionReadInput(BaseModel):
    requests: List[WikiSectionReadItem]


class WikiSectionRead(BaseTool):
    name: str = "wiki_section_read"
    description: str = (
        "Read one or more anchored wiki sections by file_name and section_id. "
        "Provide requests as an array of {file_name, section_id} objects. "
        "Returns an array with the matching section content for each request."
    )

    args_schema: type[BaseModel] = WikiSectionReadInput
    _index_service: IndexMapService = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._index_service = IndexMapService()

    def _run(self, requests: List[WikiSectionReadItem]):
        print(f"[TOOL] Reading wiki sections - {len(requests)} request(s)")

        results = []

        # 🔥 Load index ONCE (avoid repeated disk reads)
        index_data = self._index_service.load()

        for request in requests:
            file_path = os.path.join(Config.WIKI_BASE_DIR, request.file_name)

            if not os.path.exists(file_path):
                results.append({
                    "file_name": request.file_name,
                    "section_id": request.section_id,
                    "found": False,
                    "error": f"File does not exist: {file_path}",
                })
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                results.append({
                    "file_name": request.file_name,
                    "section_id": request.section_id,
                    "found": False,
                    "error": f"Error reading file: {e}",
                })
                continue

            section_content = self._extract_section(content, request.section_id)

            if section_content is None:
                results.append({
                    "file_name": request.file_name,
                    "section_id": request.section_id,
                    "found": False,
                    "error": f"Section ID not found: {request.section_id}",
                })
                continue

            # ✅ Direct dict lookup (no service call per request)
            source_ids = index_data.get(str(request.section_id), [])

            results.append({
                "file_name": request.file_name,
                "section_id": request.section_id,
                "found": True,
                "content": section_content,
                "source_ids": source_ids,
            })

        return results

    def _extract_section(self, content: str, section_id: str):
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

        section_body = parts[anchor_idx + 1]

        return section_body.strip()