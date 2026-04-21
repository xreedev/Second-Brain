from database.sqllite_service import SQLiteService


class IndexMapService:

    def _db(self):
        return SQLiteService()

    # ----------------------------
    # LOAD (returns dict for backwards compat with WikiSectionRead)
    # ----------------------------
    def load(self) -> dict:
        db = self._db()
        try:
            return db.get_all_wiki_sections()
        finally:
            db.close()

    # ----------------------------
    # CREATE SECTIONS
    # ----------------------------
    def create_sections_and_return_ids(self, source_id: str, file_name: str, sections: list[str]):
        db = self._db()
        try:
            next_id = db.get_max_wiki_section_id() + 1
            result = []
            for content in sections:
                db.insert_wiki_section(str(next_id), str(source_id), file_name)
                result.append({"id": next_id, "content": content})
                next_id += 1
            return result
        finally:
            db.close()

    # ----------------------------
    # UPDATE SECTIONS
    # ----------------------------
    def update_sections(self, source_id: str, file_name: str, section_ids: list):
        db = self._db()
        try:
            for sid in section_ids:
                db.upsert_wiki_section(str(sid), str(source_id), file_name)
        finally:
            db.close()

    # ----------------------------
    # GET SOURCES
    # ----------------------------
    def get_sources_by_section_id(self, section_id) -> list[str]:
        db = self._db()
        try:
            return db.get_wiki_section_entry(str(section_id)).get("sources", [])
        finally:
            db.close()

    # ----------------------------
    # GET FILE NAME
    # ----------------------------
    def get_file_name_by_section_id(self, section_id) -> str | None:
        db = self._db()
        try:
            return db.get_wiki_section_entry(str(section_id)).get("file_name")
        finally:
            db.close()

    # ----------------------------
    # GET FULL ENTRY
    # ----------------------------
    def get_entry(self, section_id) -> dict:
        db = self._db()
        try:
            return db.get_wiki_section_entry(str(section_id))
        finally:
            db.close()

    # ----------------------------
    # GET ALL
    # ----------------------------
    def get_all(self) -> dict:
        return self.load()
