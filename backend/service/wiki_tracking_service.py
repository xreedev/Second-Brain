import json
import os
import re

from core.config import Config
from service.index_service import IndexService
from util import fetch_file_content


class WikiTrackingService:
    def __init__(self):
        self.index_service = IndexService()

    def ensure_index_exists(self):
        if os.path.exists(Config.INDEX_FILE_PATH):
            with open(Config.INDEX_FILE_PATH, "r", encoding="utf-8") as f:
                current = f.read().strip()
            if current:
                return

        with open(Config.INDEX_FILE_PATH, "w", encoding="utf-8") as f:
            f.write("""Index of PDF Sections
| Page | Section | Section ID | Summary |
|------|---------|------------|---------|""")

    def load_source_map(self):
        return self.index_service.load()

    def write_source_map(self, source_map):
        self.index_service.write(source_map)

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

    def get_index_content(self):
        return fetch_file_content(Config.INDEX_FILE_PATH)
