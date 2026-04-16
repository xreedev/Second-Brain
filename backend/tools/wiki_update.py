from langchain.tools import BaseTool
from core.config import Config
from logger import chat_tool_logger
from pydantic import BaseModel, PrivateAttr
from typing import Optional, Literal
import os
import re
from service.index_service import IndexService


class WikiUpdateInput(BaseModel):
    file_name: str
    mode: Literal["read", "create", "update", "insert"] = "read"
    section_id: Optional[str] = None
    new_content: Optional[str] = None
    after_section_id: Optional[str] = None


class WikiUpdate(BaseTool):
    name: str = "wiki_update"
    description: str = """Read or update a wiki file. Four modes:
    - mode='read': provide only file_name. Returns full file content.
    - mode='create': provide file_name and new_content. Creates or overwrites the full file.
    - mode='update': provide file_name, section_id, new_content. Replaces that section's content.
    - mode='insert': provide file_name, after_section_id, section_id, new_content. Inserts a new section after the anchor.
    section_id can be any unique string for new sections. Existing sections should use the ids already present in the file."""

    args_schema: type[BaseModel] = WikiUpdateInput

    # PRIVATE (not exposed to LLM)
    _source_id: Optional[str] = PrivateAttr(default=None)
    _index_service: IndexService = PrivateAttr()

    def __init__(self, source_id: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self._source_id = source_id
        self._index_service = IndexService()

    def _run(
        self,
        file_name: str,
        mode: Literal["read", "create", "update", "insert"] = "read",
        section_id: Optional[str] = None,
        new_content: Optional[str] = None,
        after_section_id: Optional[str] = None,
    ):
        chat_tool_logger(
            self.name,
            f"file_name={file_name}, mode={mode}, section_id={section_id}, after_section_id={after_section_id}, source_id={self._source_id}",
        )

        file_path = os.path.join(Config.WIKI_BASE_DIR, file_name)

        # CREATE
        if mode == "create":
            if not new_content:
                return "mode='create' requires new_content"

            result = self._write(
                file_path,
                new_content.strip() + "\n",
                f"File '{file_name}' created successfully",
            )

            if not result.startswith("Error"):
                self._sync_index(file_name, new_content)

            return result

        # FILE MUST EXIST AFTER THIS
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

    # ----------------------------
    # INTERNAL HELPERS
    # ----------------------------

    def _split_on_anchors(self, content: str):
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

        parts[anchor_idx + 1] = "\n" + new_content.strip() + "\n\n"

        updated_content = "".join(parts)

        result = self._write(
            file_path,
            updated_content,
            f"Section '{section_id}' updated successfully",
        )

        if not result.startswith("Error"):
            self._sync_index(os.path.basename(file_path), updated_content, [section_id])

        return result

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

        updated_content = "".join(parts)

        result = self._write(
            file_path,
            updated_content,
            f"Section '{new_section_id}' inserted after '{after_section_id}'",
        )

        if not result.startswith("Error"):
            self._sync_index(os.path.basename(file_path), updated_content, [new_section_id])

        return result

    def _write(self, file_path, content, success_msg):
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return success_msg
        except Exception as e:
            return f"Error writing file: {e}"

    def _sync_index(self, file_name, content, touched_section_ids=None):
        """
        Sync sections to index.json if source_id exists.
        """
        if not self._source_id or file_name == "index.md":
            return

        if touched_section_ids is None:
            touched_section_ids = self._index_service.get_section_ids_from_file_content(content)

        self._index_service.add_sections_for_source(
            source_id=self._source_id,
            file_name=file_name,
            section_ids=touched_section_ids,
        )