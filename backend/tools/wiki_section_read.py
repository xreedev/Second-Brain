import os
import re
from typing import List
from langchain.tools import BaseTool
from pydantic import BaseModel, PrivateAttr

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

    _sections: list = PrivateAttr()

    def __init__(self, sections: list, **kwargs):
        super().__init__(**kwargs)
        self._sections = sections  

    def _run(self, requests: List[WikiSectionReadItem]):
        print(f"[TOOL] Reading {len(requests)} section(s)")

        results = []

        file_path = Config.INDEX_FILE_PATH  # single file

        if not os.path.exists(file_path):
            return [{
                "found": False,
                "error": f"Index file missing"
            }]

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        for request in requests:
            section_id = str(request.section_id)

            section_content = self._extract_section(content, section_id)

            if section_content is None:
                results.append({
                    "section_id": section_id,
                    "found": False,
                    "error": "Section not found"
                })
                continue

            # 🔥 Update agent state (this is YOUR goal)
            if section_id not in self._sections:
                self._sections.append(section_id)

            results.append({
                "section_id": section_id,
                "found": True,
                "content": section_content
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

        return parts[anchor_idx + 1].strip()