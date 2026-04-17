from langchain.tools import BaseTool
from core.config import Config
from logger import chat_tool_logger
from pydantic import BaseModel, PrivateAttr
from typing import Optional, Literal
import os
import re
from files_service import IndexService, IndexMapService


class WikiUpdateInput(BaseModel):
    file_name: str
    mode: Literal["read", "create", "update", "insert"] = "read"
    # create / insert: list of raw markdown strings, IDs auto-assigned
    sections: Optional[list[str | dict]] = None
    # insert only: anchor section to insert after
    after_section_id: Optional[str] = None


class WikiUpdate(BaseTool):
    name: str = "wiki_update"
    description: str = """Read or update a wiki file. Four modes:

    - mode='read':
        Provide only file_name. Returns full file content.

    - mode='create':
        Provide file_name and sections as a list of markdown strings.
        Creates or overwrites the full file. Section IDs are auto-assigned.
        Example: sections=["## Overview\\nIntro text.", "## Background\\nMore text."]

    - mode='update':
        Provide file_name and sections as a list of dicts with 'id' and 'content'.
        Replaces each matching section's content in place.
        Example: sections=[{"id": "42", "content": "## Overview\\nUpdated text."}]

    - mode='insert':
        Provide file_name, after_section_id (existing anchor), and sections as a list of
        markdown strings. Inserts new sections after the anchor. IDs are auto-assigned.
        Example: after_section_id="12", sections=["## New Section\\nContent here."]
    """

    args_schema: type[BaseModel] = WikiUpdateInput

    _source_id: Optional[str] = PrivateAttr(default=None)
    _index_service: IndexService = PrivateAttr()
    _index_map_service: IndexMapService = PrivateAttr()

    def __init__(self, source_id: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self._source_id = source_id
        self._index_service = IndexService()
        self._index_map_service = IndexMapService()

    def _run(
        self,
        file_name: str,
        mode: Literal["read", "create", "update", "insert"] = "read",
        sections: Optional[list] = None,
        after_section_id: Optional[str] = None,
    ):
        chat_tool_logger(
            self.name,
            f"file_name={file_name}, mode={mode}, after_section_id={after_section_id}, source_id={self._source_id}",
        )

        file_path = os.path.join(Config.WIKI_BASE_DIR, file_name)

        # ── CREATE ────────────────────────────────────────────────────────────
        if mode == "create":
            if not sections:
                return "mode='create' requires sections"

            # Assign IDs to all sections, record in index map
            assigned = self._assign_ids(sections)
            file_content = self._render_sections(assigned)

            result = self._write(
                file_path,
                file_content,
                f"File '{file_name}' created successfully",
            )

            if not result.startswith("Error"):
                # Pass basename so the index.md guard inside _sync_index fires correctly
                self._sync_index(os.path.basename(file_name), file_content)

            return result

        # ── FILE MUST EXIST PAST THIS POINT ───────────────────────────────────
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
            return self._update_sections(file_path, content, sections)

        if mode == "insert":
            return self._insert_sections(file_path, content, after_section_id, sections)

        return f"Unknown mode: {mode}"

    # ── INTERNAL HELPERS ──────────────────────────────────────────────────────

    def _assign_ids(self, sections: list[str]) -> list[dict]:
        """
        Call IndexMapService to get sequential IDs for a list of raw markdown strings.
        Returns [{"id": int, "content": str}, ...]
        """
        if not self._source_id:
            # No source tracking — just number them locally without persisting
            return [{"id": i + 1, "content": s} for i, s in enumerate(sections)]

        return self._index_map_service.create_sections_and_return_ids(
            source_id=self._source_id,
            sections=sections,
        )

    def _render_sections(self, assigned: list[dict]) -> str:
        """Render assigned sections into anchored markdown."""
        parts = []
        for item in assigned:
            parts.append(f'<!-- section-id: {item["id"]} -->\n{item["content"].strip()}\n')
        return "\n".join(parts) + "\n"

    def _split_on_anchors(self, content: str):
        pattern = r"(<!-- section-id: .+? -->)"
        return re.split(pattern, content)

    def _update_sections(self, file_path, content, sections):
        """Update mode: sections = [{"id": str|int, "content": str}, ...]"""
        if not sections:
            return "mode='update' requires sections"

        parts = self._split_on_anchors(content)
        updated_ids = []

        for item in sections:
            if not isinstance(item, dict) or "id" not in item or "content" not in item:
                return f"Each section must be a dict with 'id' and 'content'. Got: {item}"

            section_id = str(item["id"])
            anchor = f"<!-- section-id: {section_id} -->"

            try:
                anchor_idx = parts.index(anchor)
            except ValueError:
                return f"Section ID not found: {section_id}"

            if anchor_idx + 1 >= len(parts):
                return f"Section anchor found but no content follows it: {section_id}"

            parts[anchor_idx + 1] = "\n" + item["content"].strip() + "\n\n"
            updated_ids.append(section_id)

        updated_content = "".join(parts)

        result = self._write(
            file_path,
            updated_content,
            f"Sections {updated_ids} updated successfully",
        )

        if not result.startswith("Error"):
            self._sync_index(os.path.basename(file_path), updated_content, updated_ids)
            if self._source_id:
                self._index_map_service.update_sections(self._source_id, updated_ids)

        return result

    def _insert_sections(self, file_path, content, after_section_id, sections):
        """Insert mode: sections = list of raw markdown strings, inserted after anchor."""
        if not after_section_id or not sections:
            return "mode='insert' requires after_section_id and sections"

        after_anchor = f"<!-- section-id: {after_section_id} -->"
        if after_anchor not in content:
            return f"after_section_id not found: {after_section_id}"

        # Assign IDs for the new sections
        assigned = self._assign_ids(sections)

        parts = self._split_on_anchors(content)

        try:
            after_idx = parts.index(after_anchor)
        except ValueError:
            return f"after_section_id not found after split: {after_section_id}"

        # Build the block to insert (all new sections in order)
        new_block = "\n" + self._render_sections(assigned)

        # Insert after the content that follows the anchor (after_idx + 1 is the body)
        insert_at = after_idx + 2
        parts.insert(insert_at, new_block)

        updated_content = "".join(parts)

        new_ids = [str(item["id"]) for item in assigned]

        result = self._write(
            file_path,
            updated_content,
            f"Sections {new_ids} inserted after '{after_section_id}'",
        )

        if not result.startswith("Error"):
            self._sync_index(os.path.basename(file_path), updated_content, new_ids)

        return result

    def _write(self, file_path, content, success_msg):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return success_msg
        except Exception as e:
            return f"Error writing file: {e}"

    def _sync_index(self, file_name, content, touched_section_ids=None):
        # Always work with basename to ensure the index.md guard is reliable
        file_name = os.path.basename(file_name)

        if not self._source_id or file_name == "index.md":
            return

        if touched_section_ids is None:
            touched_section_ids = self._index_service.get_section_ids_from_file_content(content)

        self._index_service.add_sections_for_source(
            source_id=self._source_id,
            file_name=file_name,
            section_ids=touched_section_ids,
        )