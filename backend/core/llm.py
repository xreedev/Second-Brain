from core.config import Config
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

API_KEY = Config.GEMINI_API_KEY

def get_llm():

    llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        google_api_key=API_KEY
    )

    llm_gpt = ChatOpenAI(
        model="openai/gpt-4o-mini",   # or mistral, anthropic etc via gateway
        openai_api_key=Config.VERCEL_API_KEY,
        openai_api_base="https://api.vercel.ai/v1"
    )

    return llm_gpt
