import uuid
from agents import get_wiki_process_agent
from logger import chat_logger
from database.sqllite_service import SQLiteService
from vectorstores.chroma_store import ChromaStore


class ChatService:
    def __init__(self):
        self.wiki_process_agent = get_wiki_process_agent()
        self.db_service = SQLiteService()
        self.vector_store = ChromaStore()
        self.logger = chat_logger

    def chat(self, query: str):
        try:
            message_id = str(uuid.uuid4())
            self.db_service.create_message(message_id, query)

            print(f"[CHAT] message_id={message_id}")
            result = self.wiki_process_agent.run(
                prompt_text=f"user query: {query}",
                message_id=message_id,
            )
            print(f"[CHAT] Agent completed")

            response_text = result.get("text", "")
            self.db_service.update_message_response(message_id, response_text)

            section_ids = self.db_service.get_sections_for_message(message_id)
            print(f"[CHAT] Sections used: {section_ids}")

            sources = self.db_service.get_sources_for_wiki_sections(section_ids)
            print(f"[CHAT] Sources: {sources}")

            # ChromaDB metadata stores sourceid as integer strings — match that format
            source_ids_for_chroma = [str(s["id"]) for s in sources]
            documents = self.vector_store.query_by_text_and_source_ids(query, source_ids_for_chroma)

            return {
                "result": response_text,
                "sources": sources,
                "documents": documents,
            }

        except Exception as e:
            print(f"[CHAT] Error: {e}")
            return "Error processing query."
