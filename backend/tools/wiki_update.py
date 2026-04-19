import os
import re
from typing import Optional, Literal

from langchain.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
from core.config import Config
from files_service import IndexMapService, WikiTrackingService


class WikiUpdateInput(BaseModel):
    file_name: str
    mode: Literal["read", "write", "update"] = "read"
    sections: Optional[list[dict]] = Field(
        default=None,
        description=(
            "List of section objects. "
            "For write mode each object must have: "
            "'name', 'content', 'description'. "
            "For update mode also include 'id'."
        ),
    )


class WikiUpdate(BaseTool):
    name: str = "wiki_update"
    description: str = """Read or write wiki files."""

    args_schema: type[BaseModel] = WikiUpdateInput

    _source_id: Optional[str] = PrivateAttr(default=None)
    _index_map_service: IndexMapService = PrivateAttr()
    _tracking_service: WikiTrackingService = PrivateAttr()

    def __init__(self, source_id: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self._source_id = source_id
        self._index_map_service = IndexMapService()
        self._tracking_service = WikiTrackingService()

    # ─────────────────────────────────────────────────────────────

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

    # ─────────────────────────────────────────────────────────────

    def _read(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            return f"File does not exist: {file_path}"
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    # ─────────────────────────────────────────────────────────────

    def _write_mode(self, file_name: str, file_path: str, sections) -> str:
        if not sections:
            return "mode='write' requires sections"

        sections = self._normalise(sections)
        file_exists = os.path.exists(file_path)

        if file_exists:
            with open(file_path, "r", encoding="utf-8") as f:
                existing = f.read()

            existing_lower = existing.lower()
            duplicates = [
                s["name"] for s in sections
                if s["name"].lower() in existing_lower
            ]
            if duplicates:
                return f"Duplicate sections exist: {duplicates}"

        # 🔥 FIXED: pass file_name
        assigned = self._assign_ids(file_name, sections)

        new_block = self._render_sections(assigned)

        if file_exists:
            updated = existing.rstrip("\n") + "\n\n" + new_block
        else:
            updated = new_block

        result = self._persist(file_path, updated, "Write successful")

        if not result.startswith("Error"):
            self._sync_index(file_name, assigned)

        return result

    # ─────────────────────────────────────────────────────────────

    def _update_mode(self, file_name: str, file_path: str, sections) -> str:
        if not sections:
            return "mode='update' requires sections"

        sections = self._normalise(sections)

        for s in sections:
            if not s.get("id"):
                return "Each section must have an 'id'"

        if not os.path.exists(file_path):
            return f"File does not exist: {file_path}"

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        parts = self._split_on_anchors(content)
        updated_ids = []

        for section in sections:
            section_id = str(section["id"])
            anchor = f"<!-- section-id: {section_id} -->"

            if anchor not in parts:
                return f"Section ID not found: {section_id}"

            idx = parts.index(anchor)
            parts[idx + 1] = "\n" + section["content"].strip() + "\n\n"
            updated_ids.append(section_id)

        updated_content = "".join(parts)

        result = self._persist(file_path, updated_content, "Update successful")

        if not result.startswith("Error"):
            self._sync_index_full(file_name, sections)

            if self._source_id:
                # 🔥 FIXED: pass file_name
                self._index_map_service.update_sections(
                    source_id=self._source_id,
                    file_name=file_name,
                    section_ids=updated_ids,
                )

        return result

    # ─────────────────────────────────────────────────────────────

    def _assign_ids(self, file_name: str, sections: list[dict]) -> list[dict]:
        if not self._source_id:
            return [
                {**s, "id": str(i + 1)} if not s.get("id") else s
                for i, s in enumerate(sections)
            ]

        raw_contents = [s["content"] for s in sections]

        # 🔥 FIXED: pass file_name
        id_records = self._index_map_service.create_sections_and_return_ids(
            source_id=self._source_id,
            file_name=file_name,
            sections=raw_contents,
        )

        return [{**sections[i], "id": str(rec["id"])} for i, rec in enumerate(id_records)]

    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def _render_sections(assigned: list[dict]) -> str:
        parts = []
        for s in assigned:
            parts.append(
                f'<!-- section-id: {s["id"]} -->\n{s["content"].strip()}\n'
            )
        return "\n".join(parts) + "\n"

    @staticmethod
    def _split_on_anchors(content: str) -> list[str]:
        return re.split(r"(<!-- section-id: .+? -->)", content)

    # ─────────────────────────────────────────────────────────────

    def _sync_index(self, file_name: str, assigned: list[dict]):
        self._sync_index_full(file_name, assigned)

        if self._source_id:
            # 🔥 FIXED: pass file_name
            self._index_map_service.update_sections(
                source_id=self._source_id,
                file_name=file_name,
                section_ids=[str(s["id"]) for s in assigned],
            )

    def _sync_index_full(self, file_name: str, written_sections: list[dict]):
        base = os.path.basename(file_name)
        if base == "index.md":
            return

        file_path = os.path.join(Config.WIKI_BASE_DIR, file_name)

        if not os.path.exists(file_path):
            return

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = re.compile(
            r"<!-- section-id: ([^ ]+?) -->\s*\n(.*?)(?=(<!-- section-id: )|\Z)",
            re.DOTALL,
        )

        sections = []
        for match in pattern.finditer(content):
            sid = match.group(1)
            body = match.group(2).strip()

            sections.append({
                "id": sid,
                "name": f"Section {sid}",
                "description": body[:100],
            })

        self._tracking_service.add_index(file_name, sections)

    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def _normalise(sections: list) -> list[dict]:
        result = []
        for s in sections:
            if isinstance(s, BaseModel):
                s = s.model_dump()
            if not isinstance(s, dict):
                raise ValueError("Invalid section format")
            if "name" not in s or "content" not in s:
                raise ValueError("Section must have name and content")
            s.setdefault("description", "")
            result.append(s)
        return result

    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def _persist(file_path: str, content: str, success_msg: str) -> str:
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return success_msg
        except Exception as e:
            return f"Error writing file: {e}"