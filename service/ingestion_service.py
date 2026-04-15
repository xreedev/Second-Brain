from util import ArxivParser, fetch_file_content
import os
from uuid import uuid4
from core.config import Config
from agents import get_wiki_maintainer_agent_executor
from database.sqllite_service import SQLiteService
from vectorstores.chroma_store import ChromaStore

class IngestionService:
    def __init__(self):
        self.parser = ArxivParser()
        self.db_service = SQLiteService()
        self.vector_store = ChromaStore()
        self.wiki_agent_executor = get_wiki_maintainer_agent_executor()

    async def ingest_pdf(self, pdf):
        source_id = f"{pdf.filename}-{uuid4().hex}"
        file_path = os.path.join(Config.UPLOAD_DIR, pdf.filename)
        with open(file_path, "wb") as f:
            contents = pdf.file.read()
            f.write(contents)

        sections = self.parser.parse(file_path, output_format="xml")
        for section in sections:
            section["sourceid"] = source_id
        print("PDF parsed to sections successfully.", sections[:2])

        self.db_service.create_table("documents")
        self.db_service.store_sections_in_sqlite(sections, source_id)
        sections = self.db_service.get_sections_from_sqlite(source_id)
        print(f"Stored and retrieved {len(sections)} sections from SQLite for source_id={source_id}.")

        self.vector_store.store_sections_in_chroma(sections)
        print("Sections stored in ChromaDB.")

        index_current = fetch_file_content(Config.INDEX_FILE_PATH)
        print("Current index file content:", index_current[:500])

        prompt_text = (
            "pdf content: " + str(sections)
            + "\n\nindex file content: " + index_current
        )
        self.wiki_agent_executor.run(prompt_text)


