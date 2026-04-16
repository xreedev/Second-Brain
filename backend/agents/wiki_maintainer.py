from langchain.agents import create_agent
from core.llm import get_llm
from tools import IndexRead, WikiRead, WikiUpdate
from prompts import WIKI_MAINTAINER_PROMPT


class WikiMaintainerAgentExecutor:
    def __init__(self, source_id):
        llm = get_llm()
        tools = [IndexRead(), WikiRead(), WikiUpdate(source_id=source_id)]
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


def get_agent_executor(source_id):
    return WikiMaintainerAgentExecutor(source_id=source_id)
