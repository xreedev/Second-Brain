from langchain.agents import create_agent
from core.llm import get_llm
from tools import WikiRead


class WikiProcessAgent:
    def __init__(self):
        llm = get_llm()
        tools = [WikiRead()]
        self._agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=(
                "You read and reason over the wiki. "
                "Use the wiki_read tool with file_name='index.md' when you need the index."
            ),
            debug=True,
            name="wiki_process",
        )

    def run(self, prompt_text: str):
        result = self._agent.invoke(
            {"messages": [{"role": "user", "content": prompt_text}]}
        )
        messages = result.get("messages", [])
        if not messages:
            return ""
        final_message = messages[-1]
        return getattr(final_message, "content", str(final_message))

def get_agent():
    return WikiProcessAgent()
