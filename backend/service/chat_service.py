from agents import get_wiki_process_agent
from logger import chat_logger
from files_service import WikiTrackingService


class ChatService:
    def __init__(self):
        self.wiki_tracking_service = WikiTrackingService()
        self.wiki_process_agent = get_wiki_process_agent()
        self.logger = chat_logger

    def chat(self, query: str):
        try:
            print(f"[CHAT] Processing user query")
            self.wiki_tracking_service.ensure_index_exists()
            print(f"[CHAT] Index ensured to exist")
            prompt_text = f"user query: {query}"
            print(f"[CHAT] Running wiki process agent")
            result = self.wiki_process_agent.run(prompt_text)
            print(f"[CHAT] Agent completed")
            return result
        except Exception as e:
            print(f"[CHAT] Error: {e}")
            return "Error processing query."
