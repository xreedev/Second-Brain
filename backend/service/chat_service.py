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
            self.wiki_tracking_service.ensure_index_exists()
            prompt_text = f"user query: {query}"
            self.logger(f"query={query}")
            result = self.wiki_process_agent.run(prompt_text)
            self.logger(f"response={result}")
            return result
        except Exception as e:
            self.logger(f"error={e}")
            return "Error processing query."
