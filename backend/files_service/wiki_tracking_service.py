import json
import os
import re

from core.config import Config
from files_service import IndexService
from util import fetch_file_content

_INDEX_HEADER = (
    "# Wiki Index\n\n"
    "| File | Section | Section ID | Summary |\n"
    "|------|---------|------------|---------|"
)


class WikiTrackingService:
    def __init__(self):
        self.index_service = IndexService()

    # ── PUBLIC API ────────────────────────────────────────────────────────────

    def initialize_if_empty(self):
        """Create a default index.md only when the file is absent or blank."""
        index_path = Config.INDEX_FILE_PATH
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                if f.read().strip():
                    return  # already has content – leave it alone

        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(_INDEX_HEADER)

    def add_index(self, file_name: str, sections: list[dict]):
        """
        Upsert index.md rows for *file_name*.

        Each dict in *sections* must contain:
            id          – section ID (string / int)
            name        – section heading / title
            description – short summary produced by the LLM

        Existing rows for the same file are removed and replaced so that a
        create-then-update cycle never produces duplicate rows.
        """
        self.initialize_if_empty()

        index_path = Config.INDEX_FILE_PATH
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")

        # Drop every existing row that belongs to this file
        lines = [ln for ln in lines if not ln.startswith(f"| {file_name} |")]

        # Locate the table-header separator so we can insert right below it
        insert_idx = next(
            (i + 1 for i, ln in enumerate(lines) if re.match(r"^\|[-| ]+\|$", ln)),
            len(lines),  # fallback: append at end
        )

        for section in sections:
            row = (
                f"| {self._escape_cell(file_name)} "
                f"| {self._escape_cell(section['name'])} "
                f"| {self._escape_cell(str(section['id']))} "
                f"| {self._escape_cell(section.get('description', ''))} |"
            )
            lines.insert(insert_idx, row)
            insert_idx += 1

        with open(index_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def get_index_entries(self, file_name: str | None = None) -> list[dict]:
        """Parse index.md into structured rows."""
        self.initialize_if_empty()

        with open(Config.INDEX_FILE_PATH, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        entries = []
        for line in lines:
            if not line.startswith("|"):
                continue
            if re.match(r"^\|[-| ]+\|$", line):
                continue

            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) != 4:
                continue
            if cells == ["File", "Section", "Section ID", "Summary"]:
                continue

            entry = {
                "file_name": cells[0],
                "name": cells[1],
                "id": cells[2],
                "description": cells[3],
            }
            if file_name is None or entry["file_name"] == file_name:
                entries.append(entry)

        return entries

    def read_full_index(self) -> str:
        """Return the complete text of index.md, initialising it if necessary."""
        self.initialize_if_empty()
        return fetch_file_content(Config.INDEX_FILE_PATH)

    # ── INTERNAL / UTILITY ────────────────────────────────────────────────────

    def load_source_map(self):
        return self.index_service.load()

    def write_source_map(self, source_map):
        self.index_service.write(source_map)

    @staticmethod
    def _escape_cell(value: str) -> str:
        return str(value).replace("\n", " ").replace("|", "\\|").strip()

    def get_wiki_section_ids(self):
        section_ids = set()
        if not os.path.exists(Config.WIKI_BASE_DIR):
            return section_ids

        for file_name in os.listdir(Config.WIKI_BASE_DIR):
            if not file_name.endswith(".md") or file_name == "index.md":
                continue

            file_path = os.path.join(Config.WIKI_BASE_DIR, file_name)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            matches = re.findall(r"<!-- section-id: ([^ ]+?) -->", content)
            section_ids.update(matches)

        return section_ids

    def get_wiki_markdown_files(self):
        if not os.path.exists(Config.WIKI_BASE_DIR):
            return []

        markdown_files = [
            file_name
            for file_name in os.listdir(Config.WIKI_BASE_DIR)
            if file_name.endswith(".md")
        ]
        markdown_files.sort(key=lambda name: (name != "index.md", name))
        return markdown_files

    def renumber_section_ids(self):
        id_pattern = re.compile(r"<!-- section-id: ([^>]+?) -->")
        ordered_ids = []

        for file_name in self.get_wiki_markdown_files():
            file_path = os.path.join(Config.WIKI_BASE_DIR, file_name)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            for section_id in id_pattern.findall(content):
                if section_id not in ordered_ids:
                    ordered_ids.append(section_id.strip())

        id_mapping = {
            old_id: str(index)
            for index, old_id in enumerate(ordered_ids, start=1)
        }

        if not id_mapping:
            return {}

        for file_name in self.get_wiki_markdown_files():
            file_path = os.path.join(Config.WIKI_BASE_DIR, file_name)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            for index, old_id in enumerate(ordered_ids, start=1):
                content = content.replace(old_id, f"__SECTION_ID_{index}__")

            for index, old_id in enumerate(ordered_ids, start=1):
                content = content.replace(f"__SECTION_ID_{index}__", id_mapping[old_id])

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        source_map = self.load_source_map()
        if source_map:
            self.index_service.remap_section_ids(id_mapping)

        return id_mapping
