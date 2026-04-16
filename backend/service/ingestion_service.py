from util import ArxivParser
import os
from datetime import datetime
from core.config import Config
from agents import get_wiki_maintainer_agent_executor
from database.sqllite_service import SQLiteService
from service.wiki_tracking_service import WikiTrackingService
from vectorstores.chroma_store import ChromaStore
from logger import ingestion_logger

class IngestionService:
    def __init__(self):
        self.parser = ArxivParser()
        self.db_service = SQLiteService()
        self.vector_store = ChromaStore()
        self.wiki_tracking_service = WikiTrackingService()
        self.logger = ingestion_logger
        self.log = ""

    def log_info(self, *parts):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = " ".join(str(part) for part in parts)
        formatted_message = f"[{timestamp}] {message}"
        print(formatted_message)
        self.log += formatted_message + "\n"


    async def ingest_pdf(self, pdf):
        print("Ingesting pdfffffff")
        self.log = ""
        source_id = self.db_service.create_source(pdf.filename)
        self.wiki_agent_executor = get_wiki_maintainer_agent_executor(source_id=source_id)
        self.log_info(f"Assigned source_id={source_id} for the new PDF.")

        file_path = os.path.join(Config.UPLOAD_DIR, pdf.filename)
        with open(file_path, "wb") as f:
            contents = pdf.file.read()
            f.write(contents)

        sections = self.parser.parse(file_path, output_format="xml")
        for section in sections:
            section["sourceid"] = source_id
        self.log_info(f"Parsed PDF into {len(sections)} sections.")

        self.db_service.store_sections_in_sqlite(sections, source_id)
        sections = self.db_service.get_sections_from_sqlite(source_id)
        self.log_info(f"Stored and retrieved {len(sections)} sections from SQLite for source_id={source_id}.")

        self.vector_store.store_sections_in_chroma(sections)
        self.log_info("Sections stored in ChromaDB.")

        self.wiki_tracking_service.ensure_index_exists()
        index_current = self.wiki_tracking_service.get_index_content()
        self.log_info("Current index file content:", len(index_current), "characters.")

        prompt_text = (
            "pdf content: " + str(sections)
            + "\n\ncurrent source_id: " + str(source_id)
            + "\n\nindex file content: " + index_current
        )
        ingest_report = self.wiki_agent_executor.run(prompt_text)
        self.log_info("Wiki ingest report:", ingest_report)

        self.logger(self.log.rstrip())
