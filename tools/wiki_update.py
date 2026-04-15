from langchain.tools import BaseTool
from core.config import Config
from pydantic import BaseModel
from typing import Optional, Literal
import os
import re


class WikiUpdateInput(BaseModel):
    file_name: str
    mode: Literal["read", "update", "insert"] = "read"
    section_id: Optional[str] = None
    new_content: Optional[str] = None
    after_section_id: Optional[str] = None


class WikiUpdate(BaseTool):
    name: str = "wiki_update"
    description: str = """Read or update a wiki file. Three modes:
    - mode='read': provide only file_name. Returns full file content.
    - mode='update': provide file_name, section_id, new_content. Replaces that section's content.
    - mode='insert': provide file_name, after_section_id, section_id, new_content. Inserts a new section after the anchor.
    section_id format: page-slug#category#section-slug"""

    args_schema: type[BaseModel] = WikiUpdateInput

    def _run(
        self,
        file_name: str,
        mode: Literal["read", "update", "insert"] = "read",
        section_id: Optional[str] = None,
        new_content: Optional[str] = None,
        after_section_id: Optional[str] = None,
    ):
        file_path = os.path.join(Config.WIKI_BASE_DIR, file_name)

        if not os.path.exists(file_path):
            return f"File does not exist: {file_path}"

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return f"Error reading file: {e}"

        if mode == "read":
            return content

        if mode == "update":
            return self._update_section(file_path, content, section_id, new_content)

        if mode == "insert":
            return self._insert_section(file_path, content, after_section_id, section_id, new_content)

        return f"Unknown mode: {mode}"

    def _split_on_anchors(self, content: str):
        """Split file into parts, keeping anchor comments as list elements."""
        pattern = r"(<!-- section-id: .+? -->)"
        return re.split(pattern, content)

    def _update_section(self, file_path, content, section_id, new_content):
        if not section_id or not new_content:
            return "mode='update' requires section_id and new_content"

        anchor = f"<!-- section-id: {section_id} -->"
        if anchor not in content:
            return f"Section ID not found: {section_id}"

        parts = self._split_on_anchors(content)

        try:
            anchor_idx = parts.index(anchor)
        except ValueError:
            return f"Section ID not found after split: {section_id}"

        if anchor_idx + 1 >= len(parts):
            return "Section anchor found but no content follows it"

        # Replace only the content block immediately after the anchor
        parts[anchor_idx + 1] = "\n" + new_content.strip() + "\n\n"

        return self._write(file_path, "".join(parts), f"Section '{section_id}' updated successfully")

    def _insert_section(self, file_path, content, after_section_id, new_section_id, new_content):
        if not after_section_id or not new_section_id or not new_content:
            return "mode='insert' requires after_section_id, section_id, and new_content"

        after_anchor = f"<!-- section-id: {after_section_id} -->"
        if after_anchor not in content:
            return f"after_section_id not found: {after_section_id}"

        new_anchor = f"<!-- section-id: {new_section_id} -->"
        if new_anchor in content:
            return f"section_id already exists, use mode='update' instead: {new_section_id}"

        parts = self._split_on_anchors(content)

        try:
            after_idx = parts.index(after_anchor)
        except ValueError:
            return f"after_section_id not found after split: {after_section_id}"


        new_block = f"\n<!-- section-id: {new_section_id} -->\n{new_content.strip()}\n\n"

        insert_at = after_idx + 2 
        parts.insert(insert_at, new_block)

        return self._write(file_path, "".join(parts), f"Section '{new_section_id}' inserted after '{after_section_id}'")

    def _write(self, file_path, content, success_msg):
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return success_msg
        except Exception as e:
            return f"Error writing file: {e}"
