from langchain.agents import create_agent

from core.llm import get_llm
from prompts import WIKI_PROCESS_PROMPT
from tools import IndexRead, WikiSectionRead


class WikiProcessAgent:
    def __init__(self):
        self._llm = get_llm()

    def run(self, prompt_text: str):
        sections = []

        tools = [
            IndexRead(),
            WikiSectionRead(sections=sections)
        ]

        agent = create_agent(
            model=self._llm,
            tools=tools,
            system_prompt=WIKI_PROCESS_PROMPT,
            debug=True,
            name="wiki_process",
        )

        result = agent.invoke(
            {"messages": [{"role": "user", "content": prompt_text}]}
        )

        messages = result.get("messages", [])
        if not messages:
            return {"text": "", "sections": []}

        final_message = messages[-1]

        return {
            "text": getattr(final_message, "content", str(final_message)),
            "sections": sections 
        }


def get_agent():
    return WikiProcessAgent()