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
            print(f"[CHAT] Processing user query")
            prompt_text = f"user query: {query}"
            print(f"[CHAT] Running wiki process agent")
            result = self.wiki_process_agent.run(prompt_text)
            print(f"[CHAT] Agent completed")
            section_ids = result.get("sections", [])
            sources = self.db_service.get_source_files_by_section_ids(section_ids)
            documents = self.vector_store.query_by_text_and_source_ids(query, sources)
            print(f"[CHAT] Result: {result}")
            print(f"[CHAT] Sources: {sources}")
            return {"result": result.get("text"), "sources": sources, "documents": documents}
        
        except Exception as e:
            
            print(f"[CHAT] Error: {e}")
            return "Error processing query."
