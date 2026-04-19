import json
import os
from core.config import Config


class IndexMapService:
    def __init__(self):
        self.file_path = Config.INDEX_MAP_FILE_PATH

    # ----------------------------
    # LOAD
    # ----------------------------
    def load(self) -> dict:
        if not os.path.exists(self.file_path):
            self._save({})
            return {}

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                raw = f.read().strip()

            if not raw:
                self._save({})
                return {}

            data = json.loads(raw)

            if not isinstance(data, dict):
                self._save({})
                return {}

            return data

        except (json.JSONDecodeError, OSError):
            self._save({})
            return {}

    # ----------------------------
    # SAVE (atomic recommended later)
    # ----------------------------
    def _save(self, data):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ----------------------------
    # CREATE SECTIONS
    # ----------------------------
    def create_sections_and_return_ids(self, source_id: str, file_name: str, sections: list[str]):
        data = self.load()

        existing_ids = [int(k) for k in data.keys()] if data else []
        next_id = max(existing_ids) + 1 if existing_ids else 1

        result = []

        for content in sections:
            section_id = next_id

            data[str(section_id)] = {
                "sources": [str(source_id)],
                "file_name": file_name
            }

            result.append({
                "id": section_id,
                "content": content
            })

            next_id += 1

        self._save(data)
        return result

    # ----------------------------
    # UPDATE SECTIONS
    # ----------------------------
    def update_sections(self, source_id: str, file_name: str, section_ids: list[int | str]):
        data = self.load()

        for sid in section_ids:
            key = str(sid)

            if key in data:
                entry = data[key]

                # Ensure structure
                if "sources" not in entry:
                    entry["sources"] = []

                if str(source_id) not in entry["sources"]:
                    entry["sources"].append(str(source_id))

                # Update filename if needed
                entry["file_name"] = file_name

            else:
                data[key] = {
                    "sources": [str(source_id)],
                    "file_name": file_name
                }

        self._save(data)

    # ----------------------------
    # GET SOURCES
    # ----------------------------
    def get_sources_by_section_id(self, section_id: int | str) -> list[str]:
        data = self.load()
        entry = data.get(str(section_id), {})
        return entry.get("sources", [])

    # ----------------------------
    # GET FILE NAME
    # ----------------------------
    def get_file_name_by_section_id(self, section_id: int | str) -> str | None:
        data = self.load()
        entry = data.get(str(section_id), {})
        return entry.get("file_name")

    # ----------------------------
    # GET FULL ENTRY
    # ----------------------------
    def get_entry(self, section_id: int | str) -> dict:
        data = self.load()
        return data.get(str(section_id), {})

    # ----------------------------
    # GET ALL
    # ----------------------------
    def get_all(self) -> dict:
        return self.load()