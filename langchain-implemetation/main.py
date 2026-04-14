from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain.messages import   HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview", 
    google_api_key=API_KEY
)

literary_agent = create_agent(
    model=llm,
    system_prompt="You are an AI assistant tasked with analyzing literary works."
)

result = literary_agent.invoke(
    {"messages": [HumanMessage(content="Analyze the major themes in Pride and Prejudice.")]}
)

print(result)