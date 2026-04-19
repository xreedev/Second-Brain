from agents import get_wiki_process_agent
from logger import chat_logger


class ChatService:
    def __init__(self):
        self.wiki_process_agent = get_wiki_process_agent()
        self.logger = chat_logger

    def chat(self, query: str):
        try:
            print(f"[CHAT] Processing user query")
            prompt_text = f"user query: {query}"
            print(f"[CHAT] Running wiki process agent")
            result = self.wiki_process_agent.run(prompt_text)
            print(f"[CHAT] Agent completed")
            result = result[0]
            print(f"[CHAT] Result: {result}")
            return result.get("text")
        except Exception as e:
            
            print(f"[CHAT] Error: {e}")
            return "Error processing query."
