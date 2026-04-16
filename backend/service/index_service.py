import json
from core.config import Config

class IndexService:
    def get_info_from_sectionid(section_id: str):
        with open(Config.INDEX_FILE_PATH, "r", encoding="utf-8") as f:
            index_content = f.read()
            index_json = json.loads(index_content)
            result = next((x for x in index_json if x.get("id") == section_id), None)
            result = result["source_id"] if result else None
        return result

    def add_sourceid_to_sectionid(section_id: str, source_id: str):
        index_json = []
        with open(Config.INDEX_FILE_PATH, "r", encoding="utf-8") as f:
            index_content = f.read()
            index_json = json.loads(index_content)
    
        for item in index_json:
            if item.get("id") == section_id:
                item["source_id"] = item["source_id"].append(source_id)
                break
    
        with open(Config.INDEX_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(index_json, f, indent=2)

    def load(self):
        with open(Config.INDEX_MAP_FILE_PATH, "r", encoding="utf-8") as f:
            index_content = f.read()
            return json.loads(index_content)