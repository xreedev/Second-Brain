import re
from database.sqllite_service import SQLiteService


class IndexService:

    def _db(self):
        return SQLiteService()

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
        db = self._db()
        try:
            return db.get_source_ids_for_section(section_id)
        finally:
            db.close()

    # ----------------------------
    # ADD SOURCE ID TO SECTION
    # ----------------------------
    def add_sourceid_to_sectionid(self, section_id: str, source_id: str):
        db = self._db()
        try:
            db.add_section_source_mapping(section_id, source_id)
        finally:
            db.close()

    # ----------------------------
    # ADD MULTIPLE SECTIONS FOR SOURCE
    # ----------------------------
    def add_sections_for_source(self, source_id: str, file_name: str, section_ids):
        db = self._db()
        try:
            for section_id in section_ids:
                db.add_section_source_mapping(section_id, source_id)
        finally:
            db.close()

    # ----------------------------
    # LOAD FULL MAP (used by WikiTrackingService)
    # ----------------------------
    def load(self) -> dict:
        db = self._db()
        try:
            return db.get_all_wiki_sections()
        finally:
            db.close()

    # ----------------------------
    # WRITE FULL MAP (used by WikiTrackingService)
    # ----------------------------
    def write(self, source_map: dict):
        db = self._db()
        try:
            db.replace_all_section_entries(source_map)
        finally:
            db.close()

    # ----------------------------
    # REMAP SECTION IDS (used by WikiTrackingService.renumber_section_ids)
    # ----------------------------
    def remap_section_ids(self, id_mapping: dict):
        db = self._db()
        try:
            db.remap_section_ids(id_mapping)
        finally:
            db.close()
