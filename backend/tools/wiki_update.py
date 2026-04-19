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
            "'name' (section heading), "
            "'content' (full markdown body), "
            "'description' (1-2 sentence summary for the index). "
            "For update mode also include 'id' (the existing section ID to replace)."
        ),
    )


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
        - Will REJECT sections whose heading already exists in the file.
          Use mode='update' with the existing section ID instead.
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

    # ── write (create-or-append) ──────────────────────────────────────────────

    def _write_mode(self, file_name: str, file_path: str, sections) -> str:
        if not sections:
            return "mode='write' requires sections"

        sections = self._normalise(sections)
        file_exists = os.path.exists(file_path)

        if file_exists:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    existing = f.read()
            except Exception as e:
                return f"Error reading file: {e}"

            # ── Duplicate guard ───────────────────────────────────────────────
            existing_lower = existing.lower()
            duplicates = [
                s["name"] for s in sections
                if s["name"].lower() in existing_lower
            ]
            if duplicates:
                return (
                    f"Aborted: sections already exist in '{file_name}': {duplicates}. "
                    f"Read the file with mode='read' to get the section IDs, "
                    f"then use mode='update' to replace them."
                )
            # ─────────────────────────────────────────────────────────────────

            assigned = self._assign_ids(sections)
            new_block = self._render_sections(assigned)
            updated = existing.rstrip("\n") + "\n\n" + new_block
            result = self._persist(
                file_path, updated,
                f"{len(assigned)} section(s) appended to '{file_name}'",
            )
        else:
            assigned = self._assign_ids(sections)
            file_content = self._render_sections(assigned)
            result = self._persist(
                file_path, file_content,
                f"File '{file_name}' created successfully",
            )

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
                return (
                    f"mode='update' requires an 'id' on every section. "
                    f"Missing on: {s.get('name')}"
                )

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
        result = self._persist(
            file_path, updated_content,
            f"Sections {updated_ids} updated in '{file_name}'",
        )

        if not result.startswith("Error"):
            self._sync_index_full(file_name, written_sections=sections)

            if self._source_id:
                self._index_map_service.update_sections(self._source_id, updated_ids)

        return result

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _normalise(sections: list) -> list[dict]:
        """Validate and normalise incoming section dicts."""
        result = []
        for s in sections:
            if isinstance(s, BaseModel):
                s = s.model_dump()
            if not isinstance(s, dict):
                raise ValueError(f"Expected a dict for each section, got: {type(s)}")
            if "name" not in s or "content" not in s:
                raise ValueError(
                    f"Each section must have 'name' and 'content'. Got: {s}"
                )
            s.setdefault("description", "")
            result.append(s)
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
        return [{**sections[i], "id": str(rec["id"])} for i, rec in enumerate(id_records)]

    @staticmethod
    def _render_sections(assigned: list[dict]) -> str:
        """Wrap each section with its HTML anchor comment."""
        parts = []
        for s in assigned:
            parts.append(
                f'<!-- section-id: {s["id"]} -->\n{s["content"].strip()}\n'
            )
        return "\n".join(parts) + "\n"

    @staticmethod
    def _split_on_anchors(content: str) -> list[str]:
        pattern = r"(<!-- section-id: .+? -->)"
        return re.split(pattern, content)

    def _sync_index(self, file_name: str, assigned: list[dict]):
        """
        Called after a write (create / append).
        Re-reads the full file so the index always reflects every section
        present — not just the ones written in this call.
        """
        self._sync_index_full(file_name, written_sections=assigned)

        if self._source_id:
            self._index_map_service.update_sections(
                source_id=self._source_id,
                section_ids=[str(s["id"]) for s in assigned],
            )

    def _sync_index_full(self, file_name: str, written_sections: list[dict]):
        """
        Parse every section-id anchor in the file and push a complete,
        up-to-date row set to index.md.

        For sections written in this operation we have full metadata
        (name + description). For pre-existing sections we reconstruct
        metadata from the file and fall back to current index rows so
        later updates do not wipe names or summaries.
        """
        base = os.path.basename(file_name)
        if base == "index.md":
            return

        file_path = os.path.join(Config.WIKI_BASE_DIR, file_name)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return

        written_meta = {str(s["id"]): s for s in written_sections}
        existing_meta = self._read_existing_index_rows(base)
        index_sections = self._extract_index_sections(
            content=content,
            written_meta=written_meta,
            existing_meta=existing_meta,
        )

        self._tracking_service.add_index(file_name, index_sections)

    def _read_existing_index_rows(self, file_name: str) -> dict[str, dict]:
        index_path = Config.INDEX_FILE_PATH
        if not os.path.exists(index_path):
            return {}

        try:
            with open(index_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            return {}

        rows = {}
        for line in lines:
            if not line.startswith(f"| {file_name} |"):
                continue

            parts = [part.strip() for part in line.strip().strip("|").split("|")]
            if len(parts) < 4:
                continue

            _, name, section_id, description = parts[:4]
            rows[str(section_id)] = {
                "name": name,
                "description": description,
            }

        return rows

    def _extract_index_sections(
        self,
        content: str,
        written_meta: dict[str, dict],
        existing_meta: dict[str, dict],
    ) -> list[dict]:
        pattern = re.compile(
            r"<!-- section-id: ([^ ]+?) -->\s*\n(.*?)(?=(?:<!-- section-id: [^ ]+? -->)|\Z)",
            re.DOTALL,
        )

        sections = []
        for match in pattern.finditer(content):
            sid = match.group(1)
            body = match.group(2).strip()

            explicit = written_meta.get(sid, {})
            preserved = existing_meta.get(sid, {})

            name = (
                explicit.get("name")
                or self._extract_section_name(body)
                or preserved.get("name")
                or f"Section {sid}"
            )
            description = (
                explicit.get("description")
                or self._extract_section_description(body)
                or preserved.get("description", "")
            )

            sections.append({
                "id": sid,
                "name": name,
                "description": description,
            })

        return sections

    @staticmethod
    def _extract_section_name(body: str) -> str:
        frontmatter_title = re.search(
            r"^---\s*\n.*?^title:\s*\"?(.+?)\"?\s*$.*?^---\s*$",
            body,
            re.DOTALL | re.MULTILINE,
        )
        if frontmatter_title:
            return frontmatter_title.group(1).strip()

        heading = re.search(r"^#{1,6}\s+(.+?)\s*$", body, re.MULTILINE)
        if heading:
            return heading.group(1).strip()

        return ""

    @classmethod
    def _extract_section_description(cls, body: str) -> str:
        if not body:
            return ""

        body = re.sub(
            r"^---\s*\n.*?^---\s*$",
            "",
            body,
            flags=re.DOTALL | re.MULTILINE,
        )

        lines = []
        for raw_line in body.splitlines():
            line = raw_line.strip()
            if not line:
                if lines:
                    break
                continue
            if line.startswith("#"):
                continue
            if line.startswith("<!--"):
                continue
            lines.append(line)

        summary = " ".join(lines).strip()
        if not summary:
            return ""

        summary = cls._strip_markdown(summary)
        return summary[:197].rstrip() + "..." if len(summary) > 200 else summary

    @staticmethod
    def _strip_markdown(text: str) -> str:
        text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)
        text = re.sub(r"[*_~]+", "", text)
        text = re.sub(r"<[^>]+>", "", text)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _persist(file_path: str, content: str, success_msg: str) -> str:
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return success_msg
        except Exception as e:
            return f"Error writing file: {e}"
