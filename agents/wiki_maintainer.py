from langchain.agents import create_agent
from core.llm import get_llm
from tools import WikiRead, WikiUpdate
from prompts import WIKI_MAINTAINER_PROMPT


class WikiMaintainerAgentExecutor:
    def __init__(self):
        llm = get_llm()
        tools = [WikiRead(), WikiUpdate()]
        self._agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=WIKI_MAINTAINER_PROMPT,
            debug=True,
            name="wiki_maintainer",
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


def get_agent_executor():
    return WikiMaintainerAgentExecutor()
