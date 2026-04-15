import json
import os
import re

from core.config import Config
from tools import WikiUpdate
from util import fetch_file_content


class WikiTrackingService:
    def __init__(self):
        self.wiki_update_tool = WikiUpdate()

    def ensure_index_exists(self):
        if os.path.exists(Config.INDEX_FILE_PATH):
            with open(Config.INDEX_FILE_PATH, "r", encoding="utf-8") as f:
                current = f.read().strip()
            if current:
                return

        self.wiki_update_tool.invoke(
            {
                "file_name": "index.md",
                "mode": "create",
                "new_content": """<!-- section-id: index#concepts#overview -->
## Concepts
| Page | Section | Section ID | Summary |
|------|---------|------------|---------|

<!-- section-id: index#methods#overview -->
## Methods
| Page | Section | Section ID | Summary |
|------|---------|------------|---------|

<!-- section-id: index#findings#overview -->
## Findings
| Page | Section | Section ID | Summary |
|------|---------|------------|---------|""",
            }
        )

    def load_source_map(self):
        map_paths = [
            os.path.join(Config.WIKI_BASE_DIR, "index.json"),
            os.path.join(Config.WIKI_BASE_DIR, "source.json"),
        ]

        for map_path in map_paths:
            if not os.path.exists(map_path):
                continue

            with open(map_path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            if not content:
                continue

            try:
                return json.loads(content)
            except json.JSONDecodeError:
                continue

        return {}

    def write_source_map(self, source_map):
        map_paths = [
            os.path.join(Config.WIKI_BASE_DIR, "index.json"),
            os.path.join(Config.WIKI_BASE_DIR, "source.json"),
        ]

        for map_path in map_paths:
            with open(map_path, "w", encoding="utf-8") as f:
                json.dump(source_map, f, indent=2, sort_keys=True)

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
            normalized_map = {}
            for source_id, section_ids in source_map.items():
                normalized_map[source_id] = [
                    id_mapping.get(str(section_id), str(section_id))
                    for section_id in section_ids
                ]

            self.write_source_map(normalized_map)

        return id_mapping

    def update_source_map(self, source_id, new_section_ids):
        source_map = self.load_source_map()
        existing_ids = set(source_map.get(source_id, []))
        existing_ids.update(new_section_ids)
        source_map[source_id] = sorted(existing_ids, key=int)
        self.write_source_map(source_map)

    def get_next_source_id(self):
        source_map = self.load_source_map()
        if not source_map:
            return "1"

        numeric_ids = []
        for source_id in source_map.keys():
            if str(source_id).isdigit():
                numeric_ids.append(int(source_id))

        if not numeric_ids:
            return "1"

        return str(max(numeric_ids) + 1)

    def get_index_content(self):
        return fetch_file_content(Config.INDEX_FILE_PATH)

