from core.config import Config
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

API_KEY = Config.GEMINI_API_KEY

def get_llm():

    llm_gemini = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        google_api_key=API_KEY
    )

    llm_gpt = ChatOpenAI(
        model="openai/gpt-4o-mini",
        openai_api_key=Config.VERCEL_API_KEY,
        openai_api_base="https://ai-gateway.vercel.sh/v1"
    )

    llm_claude = ChatAnthropic(
        model="claude-sonnet-4-6",
        anthropic_api_key=Config.CLAUDE_API_KEY
    )

    return llm_gemini