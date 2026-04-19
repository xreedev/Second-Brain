from langchain.agents import create_agent

from core.llm import get_llm
from prompts import WIKI_PROCESS_PROMPT
from tools import IndexRead, WikiSectionRead


class WikiProcessAgent:
    def __init__(self):
        llm = get_llm()
        tools = [IndexRead(), WikiSectionRead()]
        self._agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=WIKI_PROCESS_PROMPT,
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
