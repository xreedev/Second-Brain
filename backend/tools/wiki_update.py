import os
import re
from typing import Optional, Literal

from langchain.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from core.config import Config
from files_service import IndexMapService, WikiTrackingService


# ── Section schema shared by write & update ───────────────────────────────────

class SectionInput(BaseModel):
    """One wiki section as produced by the LLM."""

    id: Optional[str] = Field(
        default=None,
        description="Section ID – required for update mode; omit for write (auto-assigned).",
    )
    name: str = Field(description="Section heading / title.")
    content: str = Field(description="Full markdown body of the section.")
    description: str = Field(description="Short summary stored in the index.")


class WikiUpdateInput(BaseModel):
    file_name: str
    mode: Literal["read", "write", "update"] = "read"
    sections: Optional[list[SectionInput]] = None


# ── Tool ──────────────────────────────────────────────────────────────────────

class WikiUpdate(BaseTool):
    name: str = "wiki_update"
    description: str = """Read or write wiki files.

    Modes
    -----
    read
        Return the full content of an existing file.
        Required: file_name

    write
        Supply a list of sections (name / content / description).
        - If the file does NOT exist it is created from scratch.
        - If the file already EXISTS the sections are appended.
        Section IDs are assigned automatically.
        Required: file_name, sections

    update
        Overwrite specific sections identified by their ID.
        Each section must include id, name, content, description.
        Required: file_name, sections (each with id)
    """

    args_schema: type[BaseModel] = WikiUpdateInput

    _source_id: Optional[str] = PrivateAttr(default=None)
    _index_map_service: IndexMapService = PrivateAttr()
    _tracking_service: WikiTrackingService = PrivateAttr()

    def __init__(self, source_id: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self._source_id = source_id
        self._index_map_service = IndexMapService()
        self._tracking_service = WikiTrackingService()

    # ── Entry point ───────────────────────────────────────────────────────────

    def _run(
        self,
        file_name: str,
        mode: Literal["read", "write", "update"] = "read",
        sections: Optional[list] = None,
    ):
        print(f"[TOOL] wiki_update – file: {file_name}, mode: {mode}")

        file_path = os.path.join(Config.WIKI_BASE_DIR, file_name)

        if mode == "read":
            return self._read(file_path)

        if mode == "write":
            return self._write_mode(file_name, file_path, sections)

        if mode == "update":
            return self._update_mode(file_name, file_path, sections)

        return f"Unknown mode: {mode}"

    # ── read ──────────────────────────────────────────────────────────────────

    def _read(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            return f"File does not exist: {file_path}"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

    # ── write (create-or-append) ───────────────────────────────────────────────

    def _write_mode(self, file_name: str, file_path: str, sections) -> str:
        if not sections:
            return "mode='write' requires sections"

        sections = self._normalise(sections)

        file_exists = os.path.exists(file_path)

        if file_exists:
            # ── APPEND to existing file ───────────────────────────────────────
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    existing = f.read()
            except Exception as e:
                return f"Error reading file: {e}"

            assigned = self._assign_ids(sections)
            new_block = self._render_sections(assigned)
            updated = existing.rstrip("\n") + "\n\n" + new_block

            result = self._persist(file_path, updated, f"{len(assigned)} section(s) appended to '{file_name}'")
        else:
            # ── CREATE new file ───────────────────────────────────────────────
            assigned = self._assign_ids(sections)
            file_content = self._render_sections(assigned)
            result = self._persist(file_path, file_content, f"File '{file_name}' created successfully")

        if not result.startswith("Error"):
            self._sync_index(file_name, assigned)

        return result

    # ── update ────────────────────────────────────────────────────────────────

    def _update_mode(self, file_name: str, file_path: str, sections) -> str:
        if not sections:
            return "mode='update' requires sections"

        sections = self._normalise(sections)

        for s in sections:
            if not s.get("id"):
                return f"mode='update' requires an 'id' on every section. Missing on: {s.get('name')}"

        if not os.path.exists(file_path):
            return f"File does not exist: {file_path}"

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return f"Error reading file: {e}"

        parts = self._split_on_anchors(content)
        updated_ids = []

        for section in sections:
            section_id = str(section["id"])
            anchor = f"<!-- section-id: {section_id} -->"

            try:
                anchor_idx = parts.index(anchor)
            except ValueError:
                return f"Section ID not found: {section_id}"

            if anchor_idx + 1 >= len(parts):
                return f"Section anchor has no trailing content: {section_id}"

            parts[anchor_idx + 1] = "\n" + section["content"].strip() + "\n\n"
            updated_ids.append(section_id)

        updated_content = "".join(parts)
        result = self._persist(file_path, updated_content, f"Sections {updated_ids} updated in '{file_name}'")

        if not result.startswith("Error"):
            # Build slim dicts for index sync using LLM-supplied name/description
            index_sections = [
                {"id": str(s["id"]), "name": s["name"], "description": s["description"]}
                for s in sections
            ]
            self._tracking_service.add_index(os.path.basename(file_name), index_sections)

            if self._source_id:
                self._index_map_service.update_sections(self._source_id, updated_ids)

        return result

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _normalise(sections: list) -> list[dict]:
        """Accept either SectionInput objects or plain dicts."""
        result = []
        for s in sections:
            if isinstance(s, SectionInput):
                result.append(s.model_dump())
            elif isinstance(s, dict):
                result.append(s)
            else:
                raise ValueError(f"Unexpected section type: {type(s)}")
        return result

    def _assign_ids(self, sections: list[dict]) -> list[dict]:
        """
        Attach auto-generated IDs to sections that don't have one yet.
        Returns a new list of dicts with 'id' guaranteed to be present.
        """
        if not self._source_id:
            return [
                {**s, "id": str(i + 1)} if not s.get("id") else s
                for i, s in enumerate(sections)
            ]

        # Delegate to IndexMapService for persistent, globally-unique IDs
        raw_contents = [s["content"] for s in sections]
        id_records = self._index_map_service.create_sections_and_return_ids(
            source_id=self._source_id,
            sections=raw_contents,
        )
        # Merge assigned IDs back into the original section dicts
        return [{**sections[i], "id": str(rec["id"])} for i, rec in enumerate(id_records)]

    @staticmethod
    def _render_sections(assigned: list[dict]) -> str:
        """Wrap each section with its HTML anchor comment."""
        parts = []
        for s in assigned:
            parts.append(f'<!-- section-id: {s["id"]} -->\n{s["content"].strip()}\n')
        return "\n".join(parts) + "\n"

    @staticmethod
    def _split_on_anchors(content: str) -> list[str]:
        pattern = r"(<!-- section-id: .+? -->)"
        return re.split(pattern, content)

    def _sync_index(self, file_name: str, assigned: list[dict]):
        """Push name + description from each assigned section into index.md."""
        base = os.path.basename(file_name)
        if base == "index.md":
            return

        index_sections = [
            {"id": str(s["id"]), "name": s["name"], "description": s["description"]}
            for s in assigned
        ]
        self._tracking_service.add_index(base, index_sections)

        if self._source_id:
            self._index_map_service.add_sections_for_source(
                source_id=self._source_id,
                file_name=base,
                section_ids=[str(s["id"]) for s in assigned],
            )

    @staticmethod
    def _persist(file_path: str, content: str, success_msg: str) -> str:
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return success_msg
        except Exception as e:
            return f"Error writing file: {e}"