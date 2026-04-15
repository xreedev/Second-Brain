from core.config import Config


API_KEY = Config.GEMINI_API_KEY

def get_llm():
    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        google_api_key=API_KEY
    )

    return llm
