import json
import os
from core.config import Config


class IndexMapService:
    def __init__(self):
        self.file_path = Config.INDEX_MAP_FILE_PATH

    def load(self) -> dict:
        if not os.path.exists(self.file_path):
            self._save({})
            return {}

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                raw = f.read().strip()

            if not raw:
                # Empty file — reset
                self._save({})
                return {}

            data = json.loads(raw)

            if not isinstance(data, dict):
                # Corrupted (e.g. saved as list) — reset
                self._save({})
                return {}

            return data

        except (json.JSONDecodeError, OSError):
            self._save({})
            return {}

    def _save(self, data):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def create_sections_and_return_ids(self, source_id: str, sections: list[str]):
        """
        Assign sequential integer IDs to new sections, record source_id for each,
        and return the sections with their assigned IDs.

        sections: list of raw markdown content strings (no IDs yet)
        returns: list of {"id": int, "content": str}
        """
        data = self.load()

        # Next ID = max existing key + 1, or 1 if empty
        existing_ids = [int(k) for k in data.keys()] if data else []
        next_id = max(existing_ids) + 1 if existing_ids else 1

        result = []
        for content in sections:
            section_id = next_id
            data[str(section_id)] = [source_id]
            result.append({"id": section_id, "content": content})
            next_id += 1

        self._save(data)
        return result

    def update_sections(self, source_id: str, section_ids: list[int | str]):
        """
        Append source_id to the source list for each existing section ID.
        If a section ID isn't tracked yet, it's added.
        """
        data = self.load()
        for sid in section_ids:
            key = str(sid)
            if key in data:
                if source_id not in data[key]:
                    data[key].append(source_id)
            else:
                data[key] = [source_id]
        self._save(data)

    def get_sources_by_section_id(self, section_id: int | str) -> list[str]:
        data = self.load()
        return data.get(str(section_id), [])

    def get_all(self) -> dict:
        """Returns the full map: { section_id: [source_id, ...] }"""
        return self.load()