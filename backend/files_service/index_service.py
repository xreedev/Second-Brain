import json
import os
import re
from core.config import Config


class IndexService:

    # ----------------------------
    # LOAD INDEX FILE (SAFE)
    # ----------------------------
    def _load_index(self):
        if not os.path.exists(Config.INDEX_JSON_FILE_PATH):
            return []

        with open(Config.INDEX_JSON_FILE_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()

            if not content:
                return []

            try:
                return json.loads(content)
            except json.JSONDecodeError:
                print("WARNING: index.json corrupted, resetting")
                return []

    # ----------------------------
    # SAVE INDEX FILE (ATOMIC)
    # ----------------------------
    def _save_index(self, data):
        temp_path = Config.INDEX_JSON_FILE_PATH + ".tmp"

        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        os.replace(temp_path, Config.INDEX_JSON_FILE_PATH)

    # ----------------------------
    # EXTRACT SECTION IDS FROM CONTENT
    # ----------------------------
    def get_section_ids_from_file_content(self, content: str):
        pattern = r"<!-- section-id: (.+?) -->"
        return re.findall(pattern, content)

    # ----------------------------
    # GET SOURCE IDS FOR A SECTION
    # ----------------------------
    def get_info_from_sectionid(self, section_id: str):
        index_json = self._load_index()

        result = next(
            (x for x in index_json if x.get("id") == section_id),
            None
        )

        return result.get("source_id") if result else None

    # ----------------------------
    # ADD SOURCE ID TO SECTION
    # ----------------------------
    def add_sourceid_to_sectionid(self, section_id: str, source_id: str):
        index_json = self._load_index()
        found = False

        for item in index_json:
            if item.get("id") == section_id:
                found = True

                # Ensure list
                if not isinstance(item.get("source_id"), list):
                    item["source_id"] = (
                        [item["source_id"]] if item.get("source_id") else []
                    )

                # Avoid duplicates
                if source_id not in item["source_id"]:
                    item["source_id"].append(source_id)

                break

        # If section not found → create new entry
        if not found:
            index_json.append({
                "id": section_id,
                "source_id": [source_id]
            })

        self._save_index(index_json)

    # ----------------------------
    # ADD MULTIPLE SECTIONS FOR SOURCE
    # ----------------------------
    def add_sections_for_source(self, source_id: str, file_name: str, section_ids):
        for section_id in section_ids:
            self.add_sourceid_to_sectionid(section_id, source_id)

    # ----------------------------
    # LOAD MAP FILE (SAFE)
    # ----------------------------
    def load(self):
        if not os.path.exists(Config.INDEX_MAP_FILE_PATH):
            return {}

        with open(Config.INDEX_MAP_FILE_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()

            if not content:
                return {}

            try:
                return json.loads(content)
            except json.JSONDecodeError:
                print("WARNING: index_map.json corrupted, resetting")
                return {}